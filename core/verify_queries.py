import duckdb, json

conn = duckdb.connect("olist.db", read_only=True)
with open("data/golden_queries.json") as f:
    queries = json.load(f)

passed = 0
for q in queries:
    try:
        result = conn.execute(q["sql"]).fetchdf()
        print(f" Q{q['id']}: {len(result)} rows — {q['nl_query'][:50]}")
        passed += 1
    except Exception as e:
        print(f" Q{q['id']}: FAILED — {e}")

print(f"\n{passed}/20 passed")
conn.close()