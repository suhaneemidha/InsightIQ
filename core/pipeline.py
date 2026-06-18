# core/pipeline.py
# Main pipeline — takes a user question, runs the full system,
# returns SQL, data, insights, and confidence score.

import time
from core.retriever import (
    build_hybrid_retriever,
    retrieve_schema_with_scores,
    check_feedback_hit,
    retrieve_with_feedback
)
from core.sql_generator import generate_sql_with_retry
from core.query_engine import execute_sql
from core.insight_generator import generate_insights
from core.confidence_scorer import compute_confidence
from core.query_history import init_history_db, log_query

# Initialize the history DB when pipeline module is first imported
init_history_db()

# Build retriever once (expensive — don't rebuild per query)
retriever = build_hybrid_retriever()
print("Hybrid retriever initialized.")


def run_pipeline(question: str) -> dict:
    """
    Full pipeline from NL question to answer.

    Returns a dict with:
        question         : original question
        schema_context   : list of schema chunks used
        sql_result       : {sql, tables_used, reasoning, llm_confidence, attempts}
        execution_result : {success, data (DataFrame), error}
        insights         : list of bullet point strings
        confidence       : {score, signals}
    """

    print(f"\n[Pipeline] Question: {question}")

    # -------------------------------------------------------
    # STEP 1: Retrieve schema context (with similarity scores)
    # -------------------------------------------------------
    # retrieve_schema_with_scores returns both the text chunks
    # AND the similarity scores (floats 0-1).
    # We need the scores for the confidence scorer.

    schema_chunks, retrieval_scores = retrieve_schema_with_scores(
        question,
        retriever.dense_retriever   # pass the dense retriever
    )

    print(f"[Pipeline] Retrieved {len(schema_chunks)} schema chunks.")
    print(f"[Pipeline] Top similarity score: {retrieval_scores[0] if retrieval_scores else 'N/A'}")

    # Also get feedback-augmented context for the actual SQL generation
    full_context = retrieve_with_feedback(question, retriever)

    # -------------------------------------------------------
    # STEP 2: Check if feedback index has a relevant hit
    # -------------------------------------------------------

    feedback_hit = check_feedback_hit(question)
    print(f"[Pipeline] Feedback hit: {feedback_hit}")

    # -------------------------------------------------------
    # STEP 3: Generate SQL (with retry)
    # -------------------------------------------------------
    # generate_sql_with_retry returns:
    # {sql, tables_used, reasoning, llm_confidence, attempts}

    sql_result = generate_sql_with_retry(question, full_context)

    sql = sql_result["sql"]
    attempts = sql_result.get("attempts", 1)
    llm_confidence = sql_result.get("llm_confidence", 50)  # default 50 if missing

    print(f"[Pipeline] SQL generated in {attempts} attempt(s).")

    # -------------------------------------------------------
    # STEP 4: Execute SQL against DuckDB
    # -------------------------------------------------------

    start_time = time.time()
    execution_result = execute_sql(sql)
    execution_ms = (time.time() - start_time) * 1000  # convert to milliseconds

    print(f"[Pipeline] SQL execution: {'success' if execution_result['success'] else 'failed'} in {execution_ms:.1f}ms")

    # -------------------------------------------------------
    # STEP 5: Generate insights (only if query succeeded)
    # -------------------------------------------------------

    insights = []
    if execution_result["success"] and execution_result["data"] is not None:
        insights = generate_insights(execution_result["data"], question)
        print(f"[Pipeline] Generated {len(insights)} insights.")

    # -------------------------------------------------------
    # STEP 6: Compute confidence score
    # -------------------------------------------------------

    confidence = compute_confidence(
        retrieval_similarities=retrieval_scores,
        sql_attempts=attempts,
        llm_confidence=llm_confidence,
        feedback_hit=feedback_hit
    )

    print(f"[Pipeline] Confidence score: {confidence['score']}/100")
    print(f"[Pipeline] Signal breakdown: {confidence['signals']}")

    # -------------------------------------------------------
    # STEP 7: Log to query history (only if SQL succeeded)
    # -------------------------------------------------------

    if execution_result["success"]:
        log_query(
            nl_query=question,
            sql=sql,
            tables_used=sql_result.get("tables_used", []),
            confidence_score=confidence["score"],
            execution_ms=execution_ms
        )
        print("[Pipeline] Query logged to history.")

    # -------------------------------------------------------
    # STEP 8: Return everything
    # -------------------------------------------------------

    return {
        "question": question,
        "schema_context": full_context,
        "sql_result": sql_result,
        "execution_result": execution_result,
        "insights": insights,
        "confidence": confidence     # <-- new field
    }


# Quick manual test
if __name__ == "__main__":
    result = run_pipeline("Top 5 sellers by revenue")
    print("\n--- RESULT ---")
    print("SQL:", result["sql_result"]["sql"])
    print("Confidence:", result["confidence"])
    print("Insights:", result["insights"])