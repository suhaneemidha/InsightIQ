# confidence_scorer.py
# Computes a 0-100 confidence score for each pipeline answer.
# Called after SQL is generated and executed.

def compute_confidence(
    retrieval_similarities: list[float],
    sql_attempts: int,
    llm_confidence: float,
    feedback_hit: bool
) -> dict:
    """
    Parameters
    ----------
    retrieval_similarities : list of floats
        Cosine similarity scores of the top retrieved schema chunks.
        Example: [0.87, 0.81, 0.74]
        These come from ChromaDB when we do a similarity search.

    sql_attempts : int
        How many attempts it took to get a valid SQL.
        1 = passed on first try (good)
        2 or 3 = needed retries (bad)
        This comes from result["attempts"] in sql_generator.py

    llm_confidence : float
        The self-reported confidence from the LLM (0-100).
        This comes from result["llm_confidence"] in the JSON response.

    feedback_hit : bool
        True if the feedback_index found a similar past correction.
        False if no relevant feedback was found.
        This comes from checking retriever.py's retrieve_with_feedback.

    Returns
    -------
    dict with:
        "score"   -> final score 0-100 (float)
        "signals" -> breakdown of each signal's contribution
    """

    # -------------------------------------------------------
    # SIGNAL 1: Retrieval similarity [weight: 30%]
    # -------------------------------------------------------
    # We average the top-3 similarity scores.
    # ChromaDB returns similarities between 0 and 1.
    # We multiply by 100 to put it on a 0-100 scale.
    # Then multiply by 0.30 to apply the 30% weight.

    if retrieval_similarities:
        top_3 = retrieval_similarities[:3]     # take top 3 only
        avg_similarity = sum(top_3) / len(top_3)  # average them
        retrieval_score = avg_similarity * 100 * 0.30
    else:
        retrieval_score = 0.0

    # -------------------------------------------------------
    # SIGNAL 2: SQL validity / attempts [weight: 30%]
    # -------------------------------------------------------
    # If SQL passed on first attempt -> full 30 points
    # If it needed 1 retry (attempts=2) -> 15 points
    # If it needed 2 retries (attempts=3) or more -> 0 points

    if sql_attempts == 1:
        validity_score = 30.0
    elif sql_attempts == 2:
        validity_score = 15.0
    else:
        validity_score = 0.0

    # -------------------------------------------------------
    # SIGNAL 3: LLM self-reported confidence [weight: 20%]
    # -------------------------------------------------------
    # LLM returns a number 0-100.
    # We scale it to 0-20 by multiplying by 0.20.

    llm_score = float(llm_confidence) * 0.20

    # -------------------------------------------------------
    # SIGNAL 4: Feedback match [weight: 20%]
    # -------------------------------------------------------
    # If we found a similar past correction -> full 20 points
    # If no feedback match -> 0 points
    # (Binary because either there's a relevant correction or not)

    feedback_score = 20.0 if feedback_hit else 0.0

    # -------------------------------------------------------
    # FINAL SCORE: sum of all 4 signals
    # -------------------------------------------------------
    final_score = (
        retrieval_score
        + validity_score
        + llm_score
        + feedback_score
    )

    # Clamp to 0-100 just in case of floating point edge cases
    final_score = max(0.0, min(100.0, final_score))

    return {
        "score": round(final_score, 1),
        "signals": {
            "retrieval": round(retrieval_score, 1),
            "sql_validity": round(validity_score, 1),
            "llm_confidence": round(llm_score, 1),
            "feedback_match": round(feedback_score, 1)
        }
    }