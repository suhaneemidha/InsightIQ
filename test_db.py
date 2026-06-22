from core.data_store import get_connection

conn = get_connection()

result = conn.execute("""
SELECT order_estimated_delivery_date
FROM orders
LIMIT 5;
""").fetchdf()

print(result)

conn.close()