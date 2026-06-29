# core/semantic_cache.py
# Semantic cache: stores past NL→SQL results and retrieves them
# when a similar question is asked again (cosine similarity > 0.95).

import sqlite3
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from datetime import datetime
import re

DB_PATH     = "semantic_cache.db"
EMBED_MODEL = "all-MiniLM-L6-v2"
SIM_THRESHOLD = 0.90   # how similar two questions must be to count as a cache hit

embedder = SentenceTransformer(EMBED_MODEL)

class _JsonEncoder(json.JSONEncoder):
    """Handles types that default json.dumps can't serialize."""
    
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)
    
def extract_years(text):
    return re.findall(r"\b(20\d{2})\b", text)
    
def init_cache_db():
    """
    Creates the cache table in SQLite if it doesn't exist.
    Call once at startup.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_cache (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nl_query  TEXT,
            embedding TEXT,
            sql       TEXT,
            result_json TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def _load_all_entries() -> list[dict]:
    """
    Loads every cached entry from SQLite.
    Returns list of dicts with keys: nl_query, embedding, sql, result_json
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT nl_query, embedding, sql, result_json
        FROM semantic_cache
        ORDER BY id DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()

    entries = []
    
    for row in rows:
        entries.append({
            "nl_query":    row[0],
            "embedding":   json.loads(row[1]),   # stored as JSON string, load back to list
            "sql":         row[2],
            "result_json": row[3]
        })
        
    return entries


def cache_lookup(nl_query: str) -> dict | None:
    """
    Checks if a semantically similar query has been answered before.

    Returns the cached result dict if similarity > SIM_THRESHOLD.
    Returns None if no match found (= cache miss, run the pipeline normally).

    The returned dict has:
        "sql"      : the SQL that was generated
        "cached"   : True (so the UI can show a "cached" badge)
        "cache_hit_query": the original query that was cached
    """
    
    entries = _load_all_entries()
    
    if not entries:
        return None

    # Embed the incoming query
    query_emb = embedder.encode(nl_query)

    # Compare against every cached embedding
    """for entry in entries:
        cached_emb = np.array(entry["embedding"])

        # Cosine similarity
        sim = np.dot(query_emb, cached_emb) / (
            np.linalg.norm(query_emb) * np.linalg.norm(cached_emb)
        )
        
        if sim >= SIM_THRESHOLD:
            
            print(f"[SemanticCache] HIT (sim={sim:.3f}) → '{entry['nl_query']}'")
            
            cached = json.loads(entry["result_json"])
            cached["cached"]           = True
            cached["cache_hit_query"]  = entry["nl_query"]
            
            return cached

    print(f"[SemanticCache] MISS for: '{nl_query}'")
    return None"""
    
    best_sim = -1
    best_entry = None

    for entry in entries:

        cached_emb = np.array(entry["embedding"])

        sim = np.dot(query_emb, cached_emb) / (
            np.linalg.norm(query_emb) * np.linalg.norm(cached_emb)
        )

        if sim > best_sim:
            best_sim = sim
            best_entry = entry

    print(
        f"[SemanticCache] Best match='{best_entry['nl_query']}' "
        f"(sim={best_sim:.3f})"
    )
    query_years = extract_years(nl_query)
    cached_years = extract_years(best_entry["nl_query"])
    
    if (best_sim >= SIM_THRESHOLD and query_years == cached_years):

        print(
            f"[SemanticCache] HIT (sim={best_sim:.3f}) "
            f"→ '{best_entry['nl_query']}'"
        )

        cached = json.loads(best_entry["result_json"])
        cached["cached"] = True
        cached["cache_hit_query"] = best_entry["nl_query"]

        return cached

    print(f"[SemanticCache] MISS for: '{nl_query}'")
    return None


def cache_store(nl_query: str, sql: str, pipeline_result: dict):
    """
    Stores a new query result in the semantic cache.
    Call this after a successful pipeline run.

    We store a serialisable version of the result —
    the DataFrame gets converted to a list of dicts.
    """
    embedding = embedder.encode(nl_query).tolist()

    # Convert DataFrame to list of dicts so it survives JSON serialisation
    
    exec_result = pipeline_result.get("execution_result", {})
    df          = exec_result.get("data")
    
    # Build a JSON-serialisable version of the result
    
    result_to_cache = {
        "sql":       sql,
        "sql_result": pipeline_result.get("sql_result", {}),
        "insights":  pipeline_result.get("insights", []),
        "confidence": pipeline_result.get("confidence", {}),
        "data_records": df.to_dict(orient="records") if df is not None else [],
        "row_count":    exec_result.get("row_count", len(df) if df is not None else 0),
    }
    
    
    if exec_result.get("data") is not None:
        result_to_cache["data_records"] = exec_result["data"].to_dict(orient="records")
        result_to_cache["row_count"]    = exec_result.get("row_count", 0)
    else:
        result_to_cache["data_records"] = []
        result_to_cache["row_count"]    = 0

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO semantic_cache
        (nl_query, embedding, sql, result_json, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        nl_query,
        json.dumps(embedding),
        sql,
        json.dumps(result_to_cache,cls=_JsonEncoder),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()
    print(f"[SemanticCache] Stored: '{nl_query}'")