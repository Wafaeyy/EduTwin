"""
Everything related to getting and cleaning up learner state.
"""

from src.agents.recommendation_system.config import FIELD_ALIASES, KNOWN_LEVELS, KNOWN_FORMATS, KNOWN_DURATIONS

# Stand-in for a real learner's twin_id. Team Alpha's StudentTwin generates a
# UUID per learner; until we integrate, every mock request uses this one.
MOCK_TWIN_ID = "mock-twin-0001"


def get_relevant_digital_twin_state():
    """Stands in for Team Alpha's real Digital Twin."""
    learner_state = {
        "twin_id": MOCK_TWIN_ID,
        "level": "beginner",
        "goal": "machine learning",
        "preferred_format": "video",
        "preferred_duration": "short",
    }
    return learner_state


def normalize_learner_state(raw_learner):
    """
    Adapter layer between whatever the real Digital Twin sends us and the
    clean, predictable shape the rest of our system expects.
    """
    if raw_learner is None:
        raw_learner = {}

    normalized = {}

    for standard_field, possible_names in FIELD_ALIASES.items():
        value = None
        for name in possible_names:
            if name in raw_learner and raw_learner[name] is not None:
                value = raw_learner[name]
                break
        normalized[standard_field] = value

    if normalized["level"] not in KNOWN_LEVELS:
        normalized["level"] = None
    if normalized["preferred_format"] not in KNOWN_FORMATS:
        normalized["preferred_format"] = None
    if normalized["preferred_duration"] not in KNOWN_DURATIONS:
        normalized["preferred_duration"] = None

    return normalized