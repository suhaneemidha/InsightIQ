# core/pipeline.py

import time
from core.retriever import (
    build_hybrid_retriever,
    retrieve_schema_with_scores_hyde,
)
from core.semantic_cache import init_cache_db, cache_lookup, cache_store

from core.sql_generator import generate_sql_with_retry
from core.query_engine import execute_sql
from core.insight_generator import generate_insights
from core.confidence_scorer import compute_confidence
from core.query_history import init_history_db, log_query
from core.feedback import FeedbackStore


init_history_db()
init_cache_db()

feedback_store = FeedbackStore()
retriever = build_hybrid_retriever()

print("Hybrid retriever initialized.")


def _BuildConversationContext(ConversationHistory: list) -> str:
    
    if not ConversationHistory:
        return ""
    
    RecentTurns = ConversationHistory[-3:]
    Lines = ["--- Conversation so far ---"]
    
    for Index, Turn in enumerate(RecentTurns, start=1):
        
        Lines.append(f"Turn {Index}:")
        Lines.append(f"  Q  : {Turn.get('question', '')}")
        Lines.append(f"  SQL: {Turn.get('sql', '')}")
        Lines.append(f"  Result (first rows):\n{Turn.get('result', '(no result)')}")
        
    Lines.append("--- End of conversation ---")
    Lines.append("Use the above context to resolve references like 'this customer', 'that ID', etc.")
    
    return "\n".join(Lines)


def run_pipeline(question: str, ConversationHistory: list = None) -> dict:
    
    if ConversationHistory is None:
        ConversationHistory = []

    print(f"\n[Pipeline] Question: {question}")

    # --------------------------------------------------
    # CACHE CHECK — before doing any real work
    # --------------------------------------------------
    
    cached = cache_lookup(question)

    if cached:
        # Reconstruct DataFrame from cached records
        
        import pandas as pd
        df = pd.DataFrame(cached.get("data_records", []))

        return {
            "question":   question,
            "sql_result": cached.get("sql_result", {"sql": cached.get("sql", "")}),
            "execution_result": {
                "success":   True,
                "data":      df,
                "row_count": cached.get("row_count", len(df)),
                "truncated": False
            },
            
            "insights":   cached.get("insights", []),
            "confidence": cached.get("confidence", {}),
            "from_cache": True,
            "cache_hit_query": cached.get("cache_hit_query", "")
        }
        
    ConversationContext = _BuildConversationContext(ConversationHistory)
    
    if ConversationContext:
        print(f"[Pipeline] Injecting {len(ConversationHistory)} prior turn(s) into prompt.")

    # ── HyDE Retrieval ─────────────────────────────────────────────────
    try:
        hyde_chunks, hyde_scores = retrieve_schema_with_scores_hyde(
            question, retriever.dense_retriever
        )
        
        retrieval_scores = hyde_scores[:3]
        print("[Pipeline] Using HyDE retrieval.")
        
    except Exception as HydeError:
        
        print(f"[Pipeline] HyDE failed ({HydeError}), using empty HyDE results.")
        
        hyde_chunks = []
        retrieval_scores = [0.5]
        

    # ── Hybrid Retrieval ───────────────────────────────────────────────
    
    hybrid_chunks = retriever.retrieve(question, top_k=6)
    full_context = list(dict.fromkeys(hyde_chunks + hybrid_chunks))

    print(f"[Pipeline] HyDE chunks: {len(hyde_chunks)}")
    print(f"[Pipeline] Hybrid chunks: {len(hybrid_chunks)}")
    print(f"[Pipeline] Combined chunks: {len(full_context)}")
    print(f"[Pipeline] Top similarity score: {retrieval_scores[0] if retrieval_scores else 'N/A'}")


    # ── Feedback Retrieval ─────────────────────────────────────────────
    
    feedback_hit = False
    
    try:
        feedback_results = feedback_store.retrieve_similar_fixes(question, k=2)
        feedback_chunks = feedback_results["documents"][0]
        
        distances = feedback_results.get("distances", [[1.0]])[0]
        
        feedback_hit = bool(distances and distances[0] < 0.35)
        full_context = list(dict.fromkeys(full_context + feedback_chunks))
        
        print(f"[Pipeline] Added {len(feedback_chunks)} feedback chunk(s). Hit: {feedback_hit}")
    
    except Exception as FeedbackError:
        print(f"[Pipeline] No feedback found: {FeedbackError}")

    full_context = full_context[:8]
    
    print(f"[Pipeline] Final context size: {len(full_context)}")
    print(f"[Pipeline] Feedback hit: {feedback_hit}")

    # ── Generate SQL ───────────────────────────────────────────────────
    
    sql_start = time.time()
    sql_result = generate_sql_with_retry(
        question, full_context, conversation_context=ConversationContext
    )
    sql_ms = (time.time() - sql_start) * 1000

    sql = sql_result.get("sql")
    if not sql:
        raise ValueError(f"SQL generator returned invalid SQL: {sql_result}")

    attempts = sql_result.get("attempts", 1)
    llm_confidence = sql_result.get("llm_confidence", 50)
    
    print(f"[Pipeline] SQL generated in {attempts} attempt(s).")


    # ── Execute SQL ────────────────────────────────────────────────────
    
    start_time = time.time()
    execution_result = execute_sql(sql)
    execution_ms = (time.time() - start_time) * 1000
    
    print(f"[Pipeline] SQL execution: {'success' if execution_result['success'] else 'failed'} in {execution_ms:.1f}ms")

    # ── Insights ───────────────────────────────────────────────────────
    
    insights = []
    
    if execution_result["success"] and execution_result["data"] is not None:
        
        insights = generate_insights(execution_result["data"], question)
        
        print(f"[Pipeline] Generated {len(insights)} insights.")


    # ── Confidence ─────────────────────────────────────────────────────
    
    confidence = compute_confidence(
        retrieval_similarities=retrieval_scores,
        sql_attempts=attempts,
        llm_confidence=llm_confidence,
        feedback_hit=feedback_hit,
    )
    
    print(f"[Pipeline] Confidence score: {confidence['score']}/100")
    print(f"[Pipeline] Signal breakdown: {confidence['signals']}")


    # ── Log ────────────────────────────────────────────────────────────
    
    if execution_result["success"]:
        
        cache_store(question, sql, {
            "sql_result":       sql_result,
            "execution_result": execution_result,
            "insights":         insights,
            "confidence":       confidence
        })
        
    log_query(
            nl_query=question,
            sql=sql,
            tables_used=sql_result.get("tables_used", []),
            confidence_score=confidence["score"],
            execution_ms=execution_ms,
            success=int(execution_result["success"]),
            error_message=execution_result.get("error", "") or "",
        )
    
    print("[Pipeline] Query logged to history.")

    return {
        "question":         question,
        "schema_context":   full_context,
        "sql_result":       sql_result,
        "execution_result": execution_result,
        "insights":         insights,
        "confidence":       confidence,
        "retrieval_scores": retrieval_scores,
        "from_cache" : False
    }