import duckdb

con = duckdb.connect("olist.db")

base = "data"

tables = {
    "customers": f"{base}/olist_customers_dataset.csv",
    "orders": f"{base}/olist_orders_dataset.csv",
    "order_items": f"{base}/olist_order_items_dataset.csv",
    "products": f"{base}/olist_products_dataset.csv",
    "sellers": f"{base}/olist_sellers_dataset.csv",
    "payments": f"{base}/olist_order_payments_dataset.csv",
    "reviews": f"{base}/olist_order_reviews_dataset.csv",
    "geolocation": f"{base}/olist_geolocation_dataset.csv",
    "category_translation": f"{base}/product_category_name_translation.csv"
}

for table, file in tables.items():
    print(f"Loading {table}...")
    con.execute(f"""
        CREATE OR REPLACE TABLE {table} AS
        SELECT * FROM read_csv_auto('{file}', ignore_errors=true)
    """)

    rows = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"✓ {rows:,} rows loaded")

con.close()

print("\nDone! Created olist.db")