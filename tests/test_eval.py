# tests/run_eval.py
# Runs all 30 golden queries through the pipeline.
# Prints a pass/fail for each one.
# Run: python tests/run_eval.py

import sys, os, json, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sql_generator import generate_sql_with_retry, validate_sql
from core.retriever import build_hybrid_retriever, retrieve_with_feedback

print("Loading retriever (takes ~20s first time)...")
retriever = build_hybrid_retriever()
print("Retriever ready.\n")

with open("data/golden_queries.json") as f:
    golden = json.load(f)

passed_first_try = 0
passed_after_retry = 0
failed = 0
results = []

for i, item in enumerate(golden):
    nl = item["nl_query"]
    expected_sql = item["sql"]

    schema_context = retrieve_with_feedback(nl, retriever)

    try:
        result = generate_sql_with_retry(nl, schema_context)
        generated_sql = result["sql"]
        attempts = result.get("attempts", 1)

        ok, error = validate_sql(generated_sql)

        if ok and attempts == 1:
            status = "✅ PASS (1st try)"
            passed_first_try += 1
        elif ok:
            status = f"⚠️  PASS (retry {attempts})"
            passed_after_retry += 1
        else:
            status = f"❌ FAIL — {error[:60]}"
            failed += 1

    except Exception as e:
        status = f"❌ ERROR — {str(e)[:60]}"
        failed += 1

    results.append({"query": nl, "status": status})
    print(f"[{i+1:02d}] {status}")
    print(f"     Q: {nl[:70]}")
    print()
    time.sleep(0.5)   # small delay to avoid Groq rate limits

print("=" * 60)
print(f"Total: {len(golden)} queries")
print(f"✅ Passed first try:    {passed_first_try}")
print(f"⚠️  Passed after retry: {passed_after_retry}")
print(f"❌ Failed:              {failed}")
print(f"\nAccuracy (valid SQL): {((passed_first_try + passed_after_retry) / len(golden)) * 100:.1f}%")
print(f"First-try accuracy:   {(passed_first_try / len(golden)) * 100:.1f}%")
print("\nSave these numbers for your Day 16 write-up.")