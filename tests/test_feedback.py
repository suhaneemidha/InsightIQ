import chromadb

client = chromadb.PersistentClient(path="vector_db")

try:
    col = client.get_collection("feedback_index")

    print("Collection exists")
    print("Documents:", col.count())

except Exception as e:
    print("Error:", e)