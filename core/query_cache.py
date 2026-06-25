import sqlite3
import json
import pandas as pd
from datetime import datetime

DB_PATH = "query_cache.db"


def init_cache_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS query_cache (
        nl_query TEXT PRIMARY KEY,
        sql TEXT,
        result_json TEXT,
        insights_json TEXT,
        confidence_json TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_cached_query(nl_query: str):

    conn = sqlite3.connect(DB_PATH)

    row = conn.execute("""
        SELECT
            sql,
            result_json,
            insights_json,
            confidence_json
        FROM query_cache
        WHERE LOWER(nl_query)=LOWER(?)
    """, (nl_query,)).fetchone()

    conn.close()

    if not row:
        return None

    return {
        "sql": row[0],
        "result": pd.DataFrame(
            json.loads(row[1])
        ),
        "insights": json.loads(row[2]),
        "confidence": json.loads(row[3])
    }


def save_cached_query(
    nl_query,
    sql,
    result_df,
    insights,
    confidence
):

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
    INSERT OR REPLACE INTO query_cache (
        nl_query,
        sql,
        result_json,
        insights_json,
        confidence_json,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        nl_query,
        sql,
        result_df.to_json(orient="records"),
        json.dumps(insights),
        json.dumps(confidence),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()