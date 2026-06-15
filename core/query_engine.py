import duckdb
import pandas as pd
from data_store import get_connection

ROW_CAP = 30

def execute_sql(sql: str) -> dict:
    """
    Executes a SQL string against olist.db.
    Returns a dict with success status, data, and error info.
    """
    try:
        conn = get_connection(read_only=True)
        df = conn.execute(sql).fetchdf()
        conn.close()

        truncated = len(df) > ROW_CAP
        if truncated:
            df = df.head(ROW_CAP)

        return {
            "success": True,
            "data": df,
            "row_count": len(df),
            "truncated": truncated
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None,
            "row_count": 0,
            "truncated": False
        }

if __name__ == "__main__":
    #Testit
    result = execute_sql(
        "SELECT order_status, COUNT(*) AS count FROM orders GROUP BY order_status ORDER BY count DESC"
    )
    
    if result["success"]:
        print(f"✅ {result['row_count']} rows returned")
        print(result["data"])
    else:
        print(f"❌ Error: {result['error']}")