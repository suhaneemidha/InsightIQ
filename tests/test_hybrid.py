from core.retriever import build_retriever, HybridRetriever
import chromadb
import json

# Dense retriever
dense_retriever = build_retriever()

# Load all chunks from ChromaDB
client = chromadb.PersistentClient(path="vector_db")
collection = client.get_collection("schema_metadata")

all_chunks = collection.get()["documents"]

# Hybrid retriever
hybrid_retriever = HybridRetriever(
    dense_retriever,
    all_chunks
)
with open("data/golden_queries.json") as f:
    golden_queries = json.load(f)

for item in golden_queries[:5]:
    
    query = item["nl_query"]

    print("\n" + "="*80)
    print("QUERY:", query)

    print("\nDENSE RETRIEVER")
    print("-"*40)

    dense_nodes = dense_retriever.retrieve(query)

    for i, node in enumerate(dense_nodes[:5], 1):
        print(f"[{i}] {node.get_content()[:150]}")

    print("\nHYBRID RETRIEVER")
    print("-"*40)

    hybrid_results = hybrid_retriever.retrieve(query)

    for i, chunk in enumerate(hybrid_results, 1):
        print(f"[{i}] {chunk[:150]}")