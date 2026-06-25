# core/query_history.py
# Logs every successful pipeline run to a SQLite database.
# Also lets you load the last N queries for use as few-shot examples.

import sqlite3
import json
from datetime import datetime

DB_PATH = "query_history.db"


def init_history_db():
    """
    Creates the query_history table if it doesn't exist.
    Call this once at app startup.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nl_query TEXT,
            sql TEXT,
            tables_used TEXT,
            confidence_score REAL,
            execution_ms REAL,
            success INTEGER,
            error_message TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_query(
    nl_query: str,
    sql: str,
    tables_used: list,
    confidence_score: float,
    execution_ms: float,
    success: int,
    error_message:str
):
    """
    Saves one query run to the history database.

    Parameters
    ----------
    nl_query        : the user's original question
    sql             : the SQL that was generated
    tables_used     : list of table names used (from sql_generator output)
    confidence_score: the final score from confidence_scorer
    execution_ms    : how long the DuckDB query took in milliseconds
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO query_history
        (
            nl_query,
            sql,
            tables_used,
            confidence_score,
            execution_ms,
            success,
            error_message,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nl_query,
            sql,
            json.dumps(tables_used),
            confidence_score,
            execution_ms,
            int(success),
            error_message,
            datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_recent_queries(limit: int = 50) -> list[dict]:
    """
    Returns the last `limit` successful queries as a list of dicts.
    Used to load history for the Streamlit history tab.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT nl_query, sql, tables_used, confidence_score, execution_ms, success,error_message,timestamp
        FROM query_history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "nl_query": row[0],
            "sql": row[1],
            "tables_used": json.loads(row[2]),
            "confidence_score": row[3],
            "execution_ms": row[4],
            "success": bool(row[5]),
            "error_message": row[6],
            "timestamp": row[7]
        })

    return result


def get_few_shot_pool(limit: int = 50) -> list[dict]:
    """
    Returns recent queries formatted as few-shot examples.
    Same format as golden_queries.json: [{"nl_query": "...", "sql": "..."}]
    So sql_generator.py can use them directly.
    """
    recent = get_recent_queries(limit)
    return [
        {"nl_query": r["nl_query"], "sql": r["sql"]}
        for r in recent
    ]