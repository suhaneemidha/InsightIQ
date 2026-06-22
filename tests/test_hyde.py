# tests/test_hyde.py
# Run from project root: python3 tests/test_hyde.py

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import chromadb
from sentence_transformers import SentenceTransformer
from core.retriever import build_retriever, retrieve_schema_with_scores
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
_embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

TEST_QUERIES = [
    {"query": "Top 5 sellers by revenue",              "expected_tables": ["order_items", "sellers"]},
    {"query": "Average delivery delay by state",        "expected_tables": ["orders", "customers"]},
    {"query": "Monthly order count for 2017 and 2018", "expected_tables": ["orders"]},
    {"query": "Which product category has the highest sales", "expected_tables": ["order_items", "products"]},
    {"query": "Average review score per category",      "expected_tables": ["reviews", "order_items", "products"]},
]


def CountTableHits(Chunks: list[str], Expected: list[str]) -> int:
    CombinedText = " ".join(Chunks).lower()
    return sum(1 for Table in Expected if Table.lower() in CombinedText)


def GenerateHypotheticalSQL(Query: str) -> str:
    prompt = f"""Write a short DuckDB SQL query that would answer this question.
Use generic table and column names. Return ONLY the SQL. No explanation. No markdown.

Question: {Query}"""
    try:
        Response = _groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=150,
        )
        SQL = Response.choices[0].message.content.strip()
        if SQL.startswith("```"):
            SQL = SQL.replace("```sql", "").replace("```", "").strip()
        return SQL
    except Exception as Error:
        print(f"[HyDE] LLM call failed: {Error}")
        return Query


def RetrieveHyde(Query: str) -> tuple[list[str], list[float]]:
    HypotheticalSQL = GenerateHypotheticalSQL(Query)
    Embedding = _embedder.encode(HypotheticalSQL).tolist()

    Collection = chromadb.PersistentClient(path="vector_db").get_collection("schema_metadata")
    Results = Collection.query(query_embeddings=[Embedding], n_results=5, include=["documents", "distances"])

    Chunks = Results["documents"][0]
    Scores = [1 / (1 + d) for d in Results["distances"][0]]
    MaxScore = max(Scores) or 1.0
    Scores = [s / MaxScore for s in Scores]
    return Chunks, Scores


def RunComparison():
    print("Building retriever...")
    Retriever = build_retriever()
    print("Ready.\n")

    print("=" * 60)
    print(f"{'Query':<45} {'Raw':>5} {'HyDE':>5} {'Winner':>8}")
    print("=" * 60)

    RawTotal, HydeTotal = 0, 0

    for Item in TEST_QUERIES:
        Query, Expected = Item["query"], Item["expected_tables"]

        RawChunks,  RawScores  = retrieve_schema_with_scores(Query, Retriever)
        HydeChunks, HydeScores = RetrieveHyde(Query)

        RawHits  = CountTableHits(RawChunks,  Expected)
        HydeHits = CountTableHits(HydeChunks, Expected)
        RawTotal  += RawHits
        HydeTotal += HydeHits

        Winner = "✅ HyDE" if HydeHits > RawHits else ("— Same" if HydeHits == RawHits else "❌ Raw")
        Short  = (Query[:43] + "..") if len(Query) > 43 else Query
        print(f"{Short:<45} {RawHits}/{len(Expected)}  {HydeHits}/{len(Expected)}   {Winner}")

    TotalExpected = sum(len(i["expected_tables"]) for i in TEST_QUERIES)
    print("=" * 60)
    print(f"{'TOTAL':<45} {RawTotal:>4}   {HydeTotal:>4}")
    print(f"\nRaw  : {RawTotal}/{TotalExpected} table hits")
    print(f"HyDE : {HydeTotal}/{TotalExpected} table hits")
    print(f"HyDE {'improved' if HydeTotal > RawTotal else 'matched' if HydeTotal == RawTotal else 'underperformed'} by {abs(HydeTotal - RawTotal)} hit(s).")
    print("\nSave these numbers for your write-up.")


if __name__ == "__main__":
    RunComparison()