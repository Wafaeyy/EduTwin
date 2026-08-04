"""
Code-based scoring: turns a (learner, resource) pair into a numeric fit
score, broken down by factor, plus a confidence measure of how much of the
learner's profile was actually available to score against.
"""


def build_score_breakdown(learner, resource):
    """
    A factor only earns points if the learner's value is known AND matches
    (Scenario B/D safety -- we never guess a match for missing data).

    Args:
        learner (dict): normalized learner state.
        resource (Resource): a single verified resource.

    Returns:
        dict: points earned per factor.
    """
    breakdown = {
        "format_match": 30 if learner["preferred_format"] is not None and learner["preferred_format"] == resource.format else 0,
        "level_match": 30 if learner["level"] is not None and learner["level"] == resource.difficulty else 0,
        "duration_match": 20 if learner["preferred_duration"] is not None and learner["preferred_duration"] == resource.duration else 0,
        "goal_relevance": 20 if learner["goal"] is not None and learner["goal"] == resource.topic else 0,
    }

    return breakdown


def calculate_score(learner, resource):
    """
    Args:
        learner (dict): normalized learner state.
        resource (Resource): a single verified resource.

    Returns:
        int: total score, 0-100.
    """
    breakdown = build_score_breakdown(learner, resource)

    return sum(breakdown.values())


def calculate_confidence(learner):
    """
    Scenario H/I: measures how much of the learner's profile was actually
    available, so we never silently pretend a low-data recommendation is
    fully personalized.

    Args:
        learner (dict): normalized learner state.

    Returns:
        float: 0.0 (nothing known) to 1.0 (everything known).
    """
    fields = [
        learner["level"],
        learner["goal"],
        learner["preferred_format"],
        learner["preferred_duration"],
    ]

    known_count = 0
    for field in fields:
        if field is not None:
            known_count += 1

    confidence = known_count / len(fields)

    return confidence