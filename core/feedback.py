import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List

import chromadb
from sentence_transformers import SentenceTransformer


DB_PATH = "feedback.db"
CHROMA_PATH = "./vector_db"
EMBED_MODEL = "all-MiniLM-L6-v2"


# ----------------------------
# SQLite Layer (structured log)
# ----------------------------
class FeedbackSQLStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_query TEXT,
                generated_sql TEXT,
                corrected_sql TEXT,
                timestamp TEXT,
                admin_id TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save(self, original_query: str, generated_sql: str,
             corrected_sql: str, admin_id: str = "admin"):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT INTO corrections
                (original_query, generated_sql, corrected_sql, timestamp, admin_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                original_query,
                generated_sql,
                corrected_sql,
                datetime.now().isoformat(),
                admin_id
            ))
            conn.commit()
        finally:
            conn.close()


# ----------------------------
# Vector Layer (semantic memory)
# ----------------------------
class FeedbackVectorStore:
    def __init__(self, path: str = CHROMA_PATH, model_name: str = EMBED_MODEL):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection("feedback_index")
        self.embedder = SentenceTransformer(model_name)

    def add(self, original_query: str, corrected_sql: str, metadata: Optional[Dict[str, Any]] = None):
        embedding = self.embedder.encode(original_query).tolist()

        doc = f"Query: {original_query}\nCorrect SQL: {corrected_sql}"

        self.collection.add(
            ids=[f"feedback_{datetime.now().timestamp()}"],
            embeddings=[embedding],
            documents=[doc],
            metadatas=[metadata or {"type": "correction"}]
        )

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        embedding = self.embedder.encode(query).tolist()

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k
        )

        return results


# ----------------------------
# Orchestrator (single API)
# ----------------------------
class FeedbackStore:
    def __init__(self):
        self.sql_store = FeedbackSQLStore()
        self.vector_store = FeedbackVectorStore()

    def save_correction(
        self,
        original_query: str,
        generated_sql: str,
        corrected_sql: str,
        admin_id: str = "admin"
    ):
        # 1. Save structured log
        self.sql_store.save(
            original_query,
            generated_sql,
            corrected_sql,
            admin_id
        )

        # 2. Save semantic memory
        self.vector_store.add(
            original_query,
            corrected_sql,
            metadata={"type": "correction", "admin_id": admin_id}
        )

    def retrieve_similar_fixes(self, query: str, k: int = 5):
        return self.vector_store.search(query, k)