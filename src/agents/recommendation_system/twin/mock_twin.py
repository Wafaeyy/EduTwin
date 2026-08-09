"""
Everything related to getting and cleaning up learner state.

Team Alpha owns the real Digital Twin. This module is our mocked stand-in
for it, plus the normalization/adapter layer that protects the rest of our
system from missing fields, alternate field names, and invalid values
(Section 16, Scenarios A, B, C, D).
"""

from config import FIELD_ALIASES, KNOWN_LEVELS, KNOWN_FORMATS, KNOWN_DURATIONS


def get_relevant_digital_twin_state():
    """
    Stands in for Team Alpha's real Digital Twin.

    Later, this function's INSIDE can be replaced with a real database call
    or API call -- nothing else in our system needs to change, because every
    other component only ever calls this function.

    Returns:
        dict: raw learner state.
    """
    learner_state = {
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

    Args:
        raw_learner (dict or None): whatever the Digital Twin gave us.

    Returns:
        dict: normalized learner state (level, goal, preferred_format,
              preferred_duration), each either a real value or None.
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