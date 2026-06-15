import chromadb
from sentence_transformers import SentenceTransformer
import json, os

METADATA_PATH = "metadata/"
VECTOR_DB_PATH = "vector_db/"

def build_vector_store():
    print("Loading embedding model (this takes ~30s first time)...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    # This model runs fully locally — no API key, no internet needed after first download

    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    
    # Delete and recreate collection so re-runs don't duplicate
    try:
        client.delete_collection("schema_metadata")
    except:
        pass
    collection = client.create_collection("schema_metadata")

    for filename in os.listdir(METADATA_PATH):
        if not filename.endswith(".json") or filename == "schema_summary.json":
            continue

        with open(os.path.join(METADATA_PATH, filename)) as f:
            meta = json.load(f)

        table_name = meta["table_name"]
        chunks = []

        # Chunk 1: Table overview
        chunks.append({
            "id": f"{table_name}__overview",
            "text": f"Table: {table_name}. {meta['description']}"
        })

        # Chunk 2: All column names and descriptions
        col_parts = [f"{col}: {desc}"for col, desc in meta["columns"].items()]        
        chunks.append({
            "id": f"{table_name}__columns",
            "text": f"Columns in {table_name}: " + " | ".join(col_parts)
        })

        # Chunk 3: Example queries (teaches the AI what kinds of questions this table answers)
        if "example_queries" in meta:
            chunks.append({
                "id": f"{table_name}__examples",
                "text": f"Example SQL for {table_name}: " + " ; ".join(meta["example_queries"])
            })

        for chunk in chunks:
            embedding = embedder.encode(chunk["text"]).tolist()
            collection.add(
                ids=[chunk["id"]],
                embeddings=[embedding],
                documents=[chunk["text"]],
                metadatas=[{"table": table_name}]
            )

        print(f"✅ Indexed: {table_name} ({len(chunks)} chunks)")

    print(f"\n✅ Total chunks in vector store: {collection.count()}")

if __name__ == "__main__":
    build_vector_store()