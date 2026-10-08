from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_PATH = BASE_DIR / "data" / "documents"
CHROMA_PATH = BASE_DIR / "data" / "chroma"
COLLECTION_NAME = "enterprise-docs"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def chunk_document(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """Split text into overlapping word-based chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between zero and chunk_size - 1")

    words = text.split()
    step = chunk_size - overlap

    return [
        " ".join(words[start : start + chunk_size])
        for start in range(0, len(words), step)
        if words[start : start + chunk_size]
    ]


def ingest_documents(documents_path: Path = DOCUMENTS_PATH) -> int:
    """Embed and store all TXT documents in ChromaDB."""
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME
    )
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    total_chunks = 0

    for document_path in sorted(documents_path.glob("*.txt")):
        text = document_path.read_text(encoding="utf-8")
        chunks = chunk_document(text)

        if not chunks:
            print(f"Skipped empty document: {document_path.name}")
            continue

        embeddings = embedding_model.encode(chunks).tolist()
        ids = [
            f"{document_path.name}-{index}"
            for index in range(len(chunks))
        ]
        metadatas = [
            {
                "source": document_path.name,
                "chunk": index,
            }
            for index in range(len(chunks))
        ]

        collection.upsert(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

        total_chunks += len(chunks)
        print(f"Ingested {len(chunks)} chunks from {document_path.name}")

    print(f"Total chunks ingested: {total_chunks}")
    print(f"ChromaDB location: {CHROMA_PATH}")
    return total_chunks


if __name__ == "__main__":
    ingest_documents()
