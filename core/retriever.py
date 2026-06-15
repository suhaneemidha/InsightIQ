# retriever.py
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb

Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def build_retriever():
    # Connect to the ChromaDB you built in Phase 1
    chroma_client = chromadb.PersistentClient(path="vector_db")
    chroma_collection = chroma_client.get_collection("schema_metadata")
    
    # Wrap it in LlamaIndex's ChromaVectorStore
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # Build the index on top of it
    index = VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context
    )
    
    # Return a retriever that fetches top 5 most relevant chunks
    return index.as_retriever(similarity_top_k=5)

def retrieve_schema(query: str, retriever) -> list[str]:
    nodes = retriever.retrieve(query)
    return [node.get_content() for node in nodes]
