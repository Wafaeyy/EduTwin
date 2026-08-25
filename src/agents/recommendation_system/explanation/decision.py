"""
Builds structured, explainable decision records. Reasons generated directly
from the score breakdown -- never invented by an LLM.
"""

from src.agents.recommendation_system.recommendation.scorer import (
    build_score_breakdown,
    calculate_confidence,
)


def create_decision_record(learner, resource):
    """One resource, scored and explained.

    The topic gate is applied here as well as in calculate_score(), so a
    record's score and its stated reasons can never disagree with each other.
    """
    breakdown = build_score_breakdown(learner, resource)

    off_topic = learner["goal"] is not None and breakdown["goal_relevance"] == 0
    score = 0 if off_topic else sum(breakdown.values())

    confidence = calculate_confidence(learner)

    reasons = []
    if off_topic:
        # Say plainly why this scored nothing. Listing a format match here
        # would be technically true and completely misleading.
        reasons.append(f"Not about '{learner['goal']}', which is what was requested")
    else:
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
        "url": resource.url,
        "format": resource.format,
        "score": score,
        "score_breakdown": breakdown,
        "reasons": reasons,
        "personalization_confidence": confidence,
    }
    return decision_record