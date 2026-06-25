# core/pipeline.py
# Main pipeline — takes a user question, runs the full system,
# returns SQL, data, insights, and confidence score.

import time
import chromadb
from core.retriever import embedder
from core.retriever import (
    build_hybrid_retriever,
    check_feedback_hit,
    retrieve_schema_with_scores_hyde 
    
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
    # HyDE retrieval returns chunks and similarity scores
    # AND the similarity scores (floats 0-1).
    # We need the scores for the confidence scorer.

    # HyDE retrieval — generates hypothetical SQL first, then embeds it
    # Falls back to regular retrieval if HyDE fails

    try:
        # ---------------------------
        # HyDE Retrieval
        # ---------------------------
        hyde_chunks, hyde_scores = retrieve_schema_with_scores_hyde(
            question,
            retriever.dense_retriever
        )
        retrieval_scores = hyde_scores[:3]
        print("[Pipeline] Using HyDE retrieval.")

    except Exception as e:

        print(
            f"[Pipeline] HyDE failed ({e}), using empty HyDE results."
        )

        hyde_chunks = []
        retrieval_scores = [0.5]
        
    # ---------------------------
    # Hybrid Retrieval (BM25 + Dense)
    # ---------------------------

    hybrid_chunks = retriever.retrieve(
        question,
        top_k=6
    )

    # ---------------------------
    # Merge both retrievals
    # Remove duplicates while preserving order
    # ---------------------------

    full_context = list(
        dict.fromkeys(
            hyde_chunks + hybrid_chunks
        )
    )

    print(
        f"[Pipeline] HyDE chunks: {len(hyde_chunks)}"
    )

    print(
        f"[Pipeline] Hybrid chunks: {len(hybrid_chunks)}"
    )

    print(
        f"[Pipeline] Combined chunks: {len(full_context)}"
    )

    print(f"[Pipeline] Top similarity score: {retrieval_scores[0] if retrieval_scores else 'N/A'}")
    feedback_chunks = []
    
    # Also get feedback-augmented context for the actual SQL generation
    try:
        
        chroma_client = chromadb.PersistentClient(
            path="vector_db"
        )

        feedback_col = chroma_client.get_collection(
            "feedback_index"
        )

        query_embedding = embedder.get_query_embedding(
            question
        )
        feedback_results = feedback_col.query(
            query_embeddings=[query_embedding],
            n_results=2
        )

        feedback_chunks = feedback_results["documents"][0]

        full_context = list(
            dict.fromkeys(
                full_context+feedback_chunks
            )
        )

        print(
            f"[Pipeline] Added {len(feedback_chunks)} feedback chunks."
        )

    except Exception as e:

        print(
            f"[Pipeline] No feedback found: {e}"
        )
        
    full_context = full_context[:8]
    print(
            f"[Pipeline] Final context size: {len(full_context)}"
        )
    # -------------------------------------------------------
    #  Check if feedback index has a relevant hit
    # -------------------------------------------------------
    
    feedback_hit = check_feedback_hit(question)
    print(f"[Pipeline] Feedback hit: {feedback_hit}")

    # -------------------------------------------------------
    # Generate SQL (with retry)
    # -------------------------------------------------------
    # generate_sql_with_retry returns:
    # {sql, tables_used, reasoning, llm_confidence, attempts}

    sql_start = time.time()

    sql_result = generate_sql_with_retry(
        question,
        full_context
    )

    sql_ms = (time.time() - sql_start) * 1000

    sql = sql_result.get("sql")
    if not sql:
        raise ValueError(
        f"SQL generator returned invalid SQL: {sql_result}"
    )
    
    attempts = sql_result.get("attempts", 1)
    llm_confidence = sql_result.get("llm_confidence", 50)  # default 50 if missing

    print(f"[Pipeline] SQL generated in {attempts} attempt(s).")

    # -------------------------------------------------------
    # Execute SQL against DuckDB
    # -------------------------------------------------------

    start_time = time.time()
    execution_result = execute_sql(sql)
    execution_ms = (time.time() - start_time) * 1000  # convert to milliseconds

    print(f"[Pipeline] SQL execution: {'success' if execution_result['success'] else 'failed'} in {execution_ms:.1f}ms")

    # -------------------------------------------------------
    # Generate insights (only if query succeeded)
    # -------------------------------------------------------

    insights = []
    if execution_result["success"] and execution_result["data"] is not None:
        insights = generate_insights(execution_result["data"], question)
        print(f"[Pipeline] Generated {len(insights)} insights.")

    # -------------------------------------------------------
    # Compute confidence score
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
    #  Log to query history (only if SQL succeeded)
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
        "confidence": confidence,    # <-- new field
        "retrieval_scores": retrieval_scores
    }
