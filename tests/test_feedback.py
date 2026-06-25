import chromadb

client = chromadb.PersistentClient(path="vector_db")
print(client.list_collections())

collection = client.get_collection("feedback_index")

print("Collection count:", collection.count())
