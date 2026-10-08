
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
CHROMA_PATH = BASE_DIR / "data" / "chroma"
COLLECTION_NAME = "enterprise-docs"
MODEL_NAME = "all-MiniLM-L6-v2"

client = chromadb.PersistentClient(path=str(CHROMA_PATH))
collection = client.get_collection(name=COLLECTION_NAME)
model = SentenceTransformer(MODEL_NAME)

query = "What are the requirements for production code changes?"
query_embedding = model.encode([query]).tolist()

results = collection.query(
    query_embeddings=query_embedding,
    n_results=min(3, collection.count()),
)

print(f"Query: {query}")
print(f"Results returned: {len(results['documents'][0])}")

for index, (document, metadata, distance) in enumerate(
    zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ),
    start=1,
):
    print(f"\nResult {index}")
    print(f"Source: {metadata['source']}")
    print(f"Distance: {distance:.4f}")
    print(f"Content: {document[:300]}...")
