import duckdb

con = duckdb.connect("olist.db")

tables = [
    "customers",
    "orders",
    "order_items",
    "products",
    "sellers",
    "payments",
    "reviews",
    "geolocation",
    "category_translation"
]

for table in tables:
    print(f"\n{'='*50}")
    print(table.upper())
    print('='*50)

    print(
        con.execute(f"DESCRIBE {table}")
        .fetchdf()
    )

con.close()