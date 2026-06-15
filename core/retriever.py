# retriever.py
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from sympy import re

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


from rank_bm25 import BM25Okapi
import numpy as np

class HybridRetriever:
    def __init__(self, dense_retriever, all_chunks: list[str]):
        self.dense_retriever = dense_retriever
        
        # Tokenize all chunks for BM25
        #tokenized = [chunk.lower().split() for chunk in all_chunks]
        import re
        tokenized = [re.findall(r"[a-zA-Z_]+", chunk.lower()) for chunk in all_chunks]
        self.bm25 = BM25Okapi(tokenized)
        self.all_chunks = all_chunks
    
    def retrieve(self, query: str, top_k: int = 6) -> list[str]:
        # --- Dense retrieval (ChromaDB) ---
        dense_nodes = self.dense_retriever.retrieve(query)
        dense_results = [node.get_content() for node in dense_nodes[:10]]
        
        # --- Sparse retrieval (BM25) ---
        #tokenized_query = query.lower().split()
        tokenized_query = re.findall(r"[a-zA-Z_]+", query.lower())
        bm25_scores = self.bm25.get_scores(tokenized_query)
        top_bm25_indices = np.argsort(bm25_scores)[::-1][:10]
        sparse_results = [self.all_chunks[i] for i in top_bm25_indices]
        
        # --- RRF Fusion ---
        scores = {}
        for rank, doc in enumerate(dense_results):
            scores[doc] = scores.get(doc, 0) + 1 / (rank + 10)
        for rank, doc in enumerate(sparse_results):
            scores[doc] = scores.get(doc, 0) + 1 / (rank + 10)
        
        # Sort by fused score, return top_k
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in ranked[:top_k]]