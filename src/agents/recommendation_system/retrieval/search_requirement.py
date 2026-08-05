"""
Translates learner state into a description of what to search for.

This module does NOT search anything and does NOT decide which resource is
best -- it only builds the search requirement.
"""


def build_search_requirement(learner):
    """
    Args:
        learner (dict): normalized learner state.

    Returns:
        dict: describes what kind of resource to look for.
    """
    search_requirement = {
        "topic": learner["goal"],
        "level": learner["level"],
        "format": learner["preferred_format"],
    }

    return search_requirement