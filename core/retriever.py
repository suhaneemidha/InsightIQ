# retriever.py

from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


from rank_bm25 import BM25Okapi

import chromadb
import numpy as np
import re

from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# embedding model used by llamaindex
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# embedding model used for feedback retrieval
embedder = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)   


def build_retriever():
    # connect to chromadb
    chroma_client = chromadb.PersistentClient(
        path="vector_db"
    )

    # load collection
    chroma_collection = chroma_client.get_collection(
        "schema_metadata"
    )

    # create vector store
    vector_store = ChromaVectorStore(
        chroma_collection=chroma_collection
    )

    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )

    # build index
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context
    )

    # return dense retriever
    return index.as_retriever(
        similarity_top_k=5
    )


def retrieve_schema(
    query: str,
    retriever
) -> list[str]:

    nodes = retriever.retrieve(query)

    return [
        node.get_content()
        for node in nodes
    ]


class HybridRetriever:

    def __init__(
        self,
        dense_retriever,
        all_chunks: list[str]
    ):
        self.dense_retriever = dense_retriever

        # tokenize chunks for bm25
        tokenized_chunks = [
            re.findall(r"[a-zA-Z0-9_]+", chunk.lower())
            for chunk in all_chunks
        ]

        self.bm25 = BM25Okapi(
            tokenized_chunks
        )

        self.all_chunks = all_chunks

    def retrieve(
        self,
        query: str,
        top_k: int = 6
    ) -> list[str]:

        # dense retrieval
        dense_nodes = self.dense_retriever.retrieve(
            query
        )

        dense_results = [
            node.get_content()
            for node in dense_nodes[:10]
        ]

        # sparse retrieval
        tokenized_query = re.findall(r"[a-zA-Z0-9_]+", query.lower())
        bm25_scores = self.bm25.get_scores(
            tokenized_query
        )

        top_bm25_indices = np.argsort(
            bm25_scores
        )[::-1][:10]

        sparse_results = [
            self.all_chunks[i]
            for i in top_bm25_indices
        ]

        # reciprocal rank fusion
        scores = {}

        for rank, doc in enumerate(
            dense_results
        ):
            scores[doc] = (
                scores.get(doc, 0)
                + 1 / (rank + 1)
            )

        for rank, doc in enumerate(
            sparse_results
        ):
            scores[doc] = (
                scores.get(doc, 0)
                + 1 / (rank + 1)
            )

        ranked = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            doc
            for doc, _
            in ranked[:top_k]
        ]


def build_hybrid_retriever():

    # build dense retriever
    dense_retriever = build_retriever()

    # load all chunks for bm25
    client = chromadb.PersistentClient(
        path="vector_db"
    )

    collection = client.get_collection(
        "schema_metadata"
    )

    all_chunks = collection.get()[
        "documents"
    ]

    return HybridRetriever(
        dense_retriever,
        all_chunks
    )


def retrieve_with_feedback(
    query: str,
    hybrid_retriever,
    top_k: int = 6
) -> list[str]:

    # retrieve schema context
    schema_chunks = hybrid_retriever.retrieve(
        query,
        top_k=top_k
    )

    try:

        # use same chromadb instance
        chroma_client = chromadb.PersistentClient(
            path="vector_db"
        )

        feedback_col = chroma_client.get_collection(
            "feedback_index"
        )

        query_embedding = embedder.get_query_embedding(
            query
        )

        feedback_results = feedback_col.query(
        query_embeddings=[query_embedding],
        n_results=2,
        include=["distances", "documents"]
)

        feedback_chunks_raw = feedback_results["documents"][0]
        distances = feedback_results.get("distances", [[1.0]])[0]

        feedback_chunks = [
            doc for doc, dist in zip(feedback_chunks_raw, distances)
        ]
        return (
            feedback_chunks+schema_chunks
        )

    except Exception as e:

        print(
            f"Feedback retrieval failed: {e}"
        )

        return schema_chunks
    
def retrieve_schema_with_scores(
    query: str,
    retriever
) -> tuple[list[str], list[float]]:
    """
    Same as retrieve_schema but also returns similarity scores.
    
    Returns
    -------
    chunks  : list of text strings (schema context)
    scores  : list of floats (0 to 1, higher = more similar)
    """
    nodes = retriever.retrieve(query)

    chunks = [node.get_content() for node in nodes]

    # node.score is the cosine similarity from ChromaDB
    # It's a float between 0 and 1
    scores = [node.score if node.score is not None else 0.0 for node in nodes]

    return chunks, scores

def check_feedback_hit(query: str) -> bool:
    """
    Returns True if feedback_index has at least one similar past correction.
    Returns False if feedback_index is empty or no relevant results found.
    """
    try:
        chroma_client = chromadb.PersistentClient(path="vector_db")
        feedback_col = chroma_client.get_collection("feedback_index")

        query_embedding = embedder.get_query_embedding(query)

        results = feedback_col.query(
            query_embeddings=[query_embedding],
            n_results=1
        )

        # If distances list is not empty and top result is close enough
        distances = results.get("distances", [[]])[0]
        if distances and distances[0] < 0.88:  
            return True
        return False

    except Exception:
        # feedback_index doesn't exist yet = no hits
        return False
    
def generate_hypothetical_sql(query: str) -> str:
    """
    HyDE Step 1: Ask the LLM to write a hypothetical SQL query
    for the user's question WITHOUT giving it any schema.
    
    We don't care if the SQL is correct — we just want something
    that looks like SQL so the embedding is closer to schema chunks.
    
    Example:
        query  = "top 5 sellers by revenue"
        output = "SELECT seller_id, SUM(price) AS revenue 
                  FROM order_items 
                  GROUP BY seller_id 
                  ORDER BY revenue DESC LIMIT 5"
    """
    prompt = f"""Write a short DuckDB SQL query that would answer this question.
Use generic table and column names — don't worry about being exactly right.
Return ONLY the SQL. No explanation. No markdown.

Question: {query}"""

    try:
        response = _groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=150   # SQL should be short
        )
        hypothetical_sql = response.choices[0].message.content.strip()

        # Strip markdown code fences if the LLM added them anyway
        if hypothetical_sql.startswith("```"):
            hypothetical_sql = hypothetical_sql.replace("```sql", "")
            hypothetical_sql = hypothetical_sql.replace("```", "")
            hypothetical_sql = hypothetical_sql.strip()

        print(f"[HyDE] Hypothetical SQL: {hypothetical_sql[:100]}...")
        return hypothetical_sql

    except Exception as e:
        print(f"[HyDE] Failed to generate hypothetical SQL: {e}")
        # Fall back to original query if LLM call fails
        return query
    
def retrieve_schema_with_scores_hyde(
    query: str,retriever
) -> tuple[list[str], list[float]]:
    """
    HyDE version of retrieve_schema_with_scores.
    
    Instead of embedding the raw NL query, we:
    1. Generate a hypothetical SQL for the query
    2. Embed the hypothetical SQL
    3. Use that embedding to search ChromaDB
    
    Returns same format as retrieve_schema_with_scores:
    (chunks, scores)
    """

    # Step 1: Generate hypothetical SQL
    hypothetical_sql = generate_hypothetical_sql(query)
    if not hypothetical_sql:
        hypothetical_sql = query

    # Step 2: Embed the hypothetical SQL using the same embedder
    # (the global `embedder` SentenceTransformer at top of this file)
    
    hyde_embedding = embedder.get_query_embedding(hypothetical_sql)

    # Step 3: Query ChromaDB directly with the HyDE embedding
    # (bypassing LlamaIndex so we can pass our own embedding)
    
    chroma_client = chromadb.PersistentClient(path="vector_db")
    collection = chroma_client.get_collection("schema_metadata")
    
    results = collection.query(
        query_embeddings=[hyde_embedding],
        n_results=5,
        include=["documents", "distances"]
    )
    chunks = results["documents"][0]
    distances = results["distances"][0]   # list of floats (lower = more similar in ChromaDB)

    # ChromaDB returns L2 distances (lower = closer).
    # Convert to similarity scores (higher = better) so our confidence scorer works.
    # Formula: similarity = 1 / (1 + distance)
    scores = [1 / (1 + d) for d in distances]
    scores = [s / max(scores) for s in scores]

    print(f"[HyDE] Top similarity after HyDE: {scores[0]:.3f} (was raw NL query before)")

    return chunks, scores