import duckdb
import os
import json

DATA_PATH = "data/"
DB_PATH = "olist.db"

def load_all_csvs():
    conn = duckdb.connect(DB_PATH)
    
    csv_files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv")]
    
    for filename in csv_files:
        table_name = filename.replace(".csv", "")
        filepath = os.path.join(DATA_PATH, filename)
        
        conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_csv_auto('{filepath}')
        """)
        
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"✅ {table_name}: {count} rows")
    
    conn.close()
    print(f"\n✅ olist.db created at {DB_PATH}")

def get_connection(read_only=True):
    """Returns a DuckDB connection. Use this everywhere else in the codebase."""
    return duckdb.connect(DB_PATH, read_only=read_only)

if __name__ == "__main__":
    load_all_csvs()