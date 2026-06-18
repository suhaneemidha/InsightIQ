# tests/test_confidence.py

import sys
import os

# This line lets Python find your core/ folder when running tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.confidence_scorer import compute_confidence


def test_weights_sum_to_100_on_perfect_input():
    """
    Perfect case: high similarity, first attempt, LLM says 100, feedback hit.
    Score should be close to 100.
    """
    result = compute_confidence(
        retrieval_similarities=[1.0, 1.0, 1.0],  # perfect similarity
        sql_attempts=1,                            # first try
        llm_confidence=100,                        # LLM is certain
        feedback_hit=True                          # feedback found
    )
    print("Perfect input score:", result)
    assert result["score"] == 100.0, f"Expected 100.0, got {result['score']}"
    print("PASSED: test_weights_sum_to_100_on_perfect_input")


def test_all_retries_failed_gives_zero_validity():
    """
    If SQL needed max retries, validity signal should be 0.
    """
    result = compute_confidence(
        retrieval_similarities=[0.8, 0.7, 0.6],
        sql_attempts=3,   # max retries = 0 points for validity
        llm_confidence=50,
        feedback_hit=False
    )
    print("Max retries score:", result)
    assert result["signals"]["sql_validity"] == 0.0, \
        f"Expected 0.0, got {result['signals']['sql_validity']}"
    print("PASSED: test_all_retries_failed_gives_zero_validity")


def test_no_feedback_gives_zero_feedback_score():
    """
    If no feedback hit, feedback signal should be 0.
    """
    result = compute_confidence(
        retrieval_similarities=[0.9, 0.8, 0.7],
        sql_attempts=1,
        llm_confidence=80,
        feedback_hit=False   # no feedback
    )
    print("No feedback score:", result)
    assert result["signals"]["feedback_match"] == 0.0, \
        f"Expected 0.0, got {result['signals']['feedback_match']}"
    print("PASSED: test_no_feedback_gives_zero_feedback_score")


def test_score_never_exceeds_100():
    """
    Score should always be clamped to 100 max.
    """
    result = compute_confidence(
        retrieval_similarities=[1.0, 1.0, 1.0, 1.0, 1.0],  # more than 3
        sql_attempts=1,
        llm_confidence=100,
        feedback_hit=True
    )
    assert result["score"] <= 100.0, f"Score exceeded 100: {result['score']}"
    print("PASSED: test_score_never_exceeds_100")


def test_empty_retrieval_gives_zero_retrieval_score():
    """
    If retrieval returned nothing, retrieval signal = 0.
    """
    result = compute_confidence(
        retrieval_similarities=[],   # nothing retrieved
        sql_attempts=1,
        llm_confidence=70,
        feedback_hit=False
    )
    assert result["signals"]["retrieval"] == 0.0, \
        f"Expected 0.0, got {result['signals']['retrieval']}"
    print("PASSED: test_empty_retrieval_gives_zero_retrieval_score")


def test_one_retry_gives_half_validity():
    """
    sql_attempts=2 should give 15.0 (half of 30).
    """
    result = compute_confidence(
        retrieval_similarities=[0.8, 0.7, 0.6],
        sql_attempts=2,
        llm_confidence=60,
        feedback_hit=False
    )
    assert result["signals"]["sql_validity"] == 15.0, \
        f"Expected 15.0, got {result['signals']['sql_validity']}"
    print("PASSED: test_one_retry_gives_half_validity")


# Run all tests
if __name__ == "__main__":
    test_weights_sum_to_100_on_perfect_input()
    test_all_retries_failed_gives_zero_validity()
    test_no_feedback_gives_zero_feedback_score()
    test_score_never_exceeds_100()
    test_empty_retrieval_gives_zero_retrieval_score()
    test_one_retry_gives_half_validity()
    print("\nAll tests passed.")