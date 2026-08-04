"""
Builds structured, explainable decision records. Every reason here is
generated directly from the score breakdown -- never invented by an LLM.
"""

from recommendation.scorer import build_score_breakdown, calculate_confidence


def create_decision_record(learner, resource):
    """
    Args:
        learner (dict): normalized learner state.
        resource (Resource): a single verified resource.

    Returns:
        dict: {"resource": ..., "score": ..., "score_breakdown": ...,
               "reasons": [...], "personalization_confidence": ...}
    """
    breakdown = build_score_breakdown(learner, resource)
    score = sum(breakdown.values())
    confidence = calculate_confidence(learner)

    reasons = []

    if breakdown["format_match"] > 0:
        reasons.append("Matches the learner's preferred format")

    if breakdown["level_match"] > 0:
        reasons.append("Matches the learner's current level")

    if breakdown["duration_match"] > 0:
        reasons.append("Matches the learner's preferred duration")

    if breakdown["goal_relevance"] > 0:
        reasons.append("Strongly matches the learner's current goal")

    if confidence < 1.0:
        reasons.append("Note: some learner preferences were unavailable, so personalization is partial")

    decision_record = {
        "resource": resource.title,
        "score": score,
        "score_breakdown": breakdown,
        "reasons": reasons,
        "personalization_confidence": confidence,
    }

    return decision_record