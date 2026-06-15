import chromadb
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="vector_db/")
collection = client.get_collection("schema_metadata")

test_queries = [
    "which state has the most delayed deliveries?",
    "top sellers by revenue",
    "average review score by product category"
]

for q in test_queries:
    emb = embedder.encode(q).tolist()
    results = collection.query(query_embeddings=[emb], n_results=3)
    print(f"\nQuery: {q}")
    for doc in results["documents"][0]:
        print(f"  → {doc[:100]}...")