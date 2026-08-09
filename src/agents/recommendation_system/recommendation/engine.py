"""
The Recommendation Engine itself: builds a decision record for every
verified resource and ranks them best-to-worst.
"""

from explanation.decision import create_decision_record


def recommend(learner, resources):
    """
    Args:
        learner (dict): normalized learner state.
        resources (list): verified resource dictionaries.

    Returns:
        list: decision record dictionaries, sorted highest score first.
    """
    decision_records = []

    for resource in resources:
        record = create_decision_record(learner, resource)
        decision_records.append(record)

    decision_records.sort(key=lambda record: record["score"], reverse=True)

    return decision_records