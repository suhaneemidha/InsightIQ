# core/test_hyde.py
# Compares retrieval precision: raw NL query vs HyDE
# Run this: python core/test_hyde.py
# Document the results in your write-up.

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.retriever import (
    build_retriever,
    retrieve_schema_with_scores,
    retrieve_schema_with_scores_hyde
)

# 5 representative queries from your golden set
TEST_QUERIES = [
    {
        "query": "Top 5 sellers by revenue",
        "expected_tables": ["order_items", "sellers"]
    },
    {
        "query": "Average delivery delay by state",
        "expected_tables": ["orders", "customers"]
    },
    {
        "query": "Monthly order count for 2017 and 2018",
        "expected_tables": ["orders"]
    },
    {
        "query": "Which product category has the highest sales",
        "expected_tables": ["order_items", "products"]
    },
    {
        "query": "Average review score per category",
        "expected_tables": ["reviews", "order_items", "products"]
    }
]


def check_tables_in_chunks(chunks: list[str], expected_tables: list[str]) -> int:
    """
    Returns how many of the expected tables appear in the retrieved chunks.
    This is our precision metric.
    """
    found = 0
    all_text = " ".join(chunks).lower()
    for table in expected_tables:
        if table.lower() in all_text:
            found += 1
    return found


def run_comparison():
    print("Building retriever...")
    dense_retriever = build_retriever()
    print("Retriever ready.\n")

    print("=" * 60)
    print(f"{'Query':<45} {'Raw':>6} {'HyDE':>6} {'Better?':>8}")
    print("=" * 60)

    raw_total = 0
    hyde_total = 0

    for item in TEST_QUERIES:
        query = item["query"]
        expected = item["expected_tables"]
        total_expected = len(expected)

        # Raw NL retrieval
        raw_chunks, raw_scores = retrieve_schema_with_scores(query, dense_retriever)
        raw_hits = check_tables_in_chunks(raw_chunks, expected)

        # HyDE retrieval
        hyde_chunks, hyde_scores = retrieve_schema_with_scores_hyde(query, dense_retriever)
        hyde_hits = check_tables_in_chunks(hyde_chunks, expected)

        raw_total += raw_hits
        hyde_total += hyde_hits

        better = "✅ HyDE" if hyde_hits > raw_hits else ("Same" if hyde_hits == raw_hits else "❌ Raw")
        short_query = query[:43] + ".." if len(query) > 43 else query

        print(f"{short_query:<45} {raw_hits}/{total_expected}  {hyde_hits}/{total_expected}   {better}")

    print("=" * 60)
    print(f"{'TOTAL':<45} {raw_total:>4}   {hyde_total:>4}")
    print(f"\nHyDE improved retrieval on {hyde_total - raw_total} more table hits.")
    print("\nSave these numbers — they go in your individual contribution write-up.")


if __name__ == "__main__":
    run_comparison()