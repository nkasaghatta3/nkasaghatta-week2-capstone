import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

CHROMA_PATH = BASE_DIR / "data" / "chroma"
COLLECTION_NAME = "enterprise-docs"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    return _embedding_model


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve the most relevant document chunks."""
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = chroma_client.get_collection(name=COLLECTION_NAME)

    result_count = min(top_k, collection.count())
    if result_count == 0:
        return []

    embedding = get_embedding_model().encode([query]).tolist()
    results = collection.query(
        query_embeddings=embedding,
        n_results=result_count,
    )

    return [
        {
            "content": document,
            "source": metadata["source"],
            "chunk": metadata["chunk"],
        }
        for document, metadata in zip(
            results["documents"][0],
            results["metadatas"][0],
        )
    ]


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Build a grounded prompt using retrieved context."""
    context_parts = [
        f"Source {index} ({chunk['source']}):\n{chunk['content']}"
        for index, chunk in enumerate(chunks, start=1)
    ]
    context = "\n\n".join(context_parts)

    return f"""
You are an enterprise documentation assistant.

Answer the question using ONLY the provided context.
If the answer is not contained in the context, say:
"I cannot find this information in the provided documents."

Do not use outside knowledge or invent policies.
Always cite the source number or numbers used, such as "Source 1".

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
""".strip()


def run(query: str) -> dict:
    """Retrieve context and generate a grounded Gemini response."""
    chunks = retrieve(query)
    prompt = build_prompt(query, chunks)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
    )

    message = response.choices[0].message
    usage = response.usage

    return {
        "answer": message.content or "",
        "chunks": chunks,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
    }
