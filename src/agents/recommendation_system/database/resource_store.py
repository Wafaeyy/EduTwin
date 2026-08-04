"""
The (mocked) verified resource catalog and the code that queries it.

Later, MOCK_RESOURCE_DATABASE gets replaced by a real database. Nothing
outside this module should ever touch the raw data directly -- everything
goes through retrieve_from_database().
"""

from models.resource import Resource

MOCK_RESOURCE_DATABASE = [
    Resource(
        title="Machine Learning for Absolute Beginners",
        url="https://example.com/ml-beginners-video",
        description="A short beginner-friendly video introduction to machine learning.",
        topic="machine learning",
        difficulty="beginner",
        format="video",
        duration="short",
    ),
    Resource(
        title="Deep Learning Specialization",
        url="https://example.com/deep-learning-course",
        description="A long, in-depth advanced course on deep learning.",
        topic="machine learning",
        difficulty="advanced",
        format="video",
        duration="long",
    ),
    Resource(
        title="Introduction to Data Structures",
        url="https://example.com/data-structures-article",
        description="A beginner article about data structures.",
        topic="data structures",
        difficulty="beginner",
        format="article",
        duration="short",
    ),
]


def retrieve_from_database(search_requirement):
    """
    Looks through the mock resource database and returns resources whose
    topic and difficulty level match the search requirement.

    If the search requirement doesn't specify a topic or level, we don't
    filter on that field at all (Scenario A/B support).

    Args:
        search_requirement (dict): output of build_search_requirement().

    Returns:
        list: matching Resource objects.
    """
    matches = []

    for resource in MOCK_RESOURCE_DATABASE:
        topic_matches = (
            search_requirement["topic"] is None
            or resource.topic == search_requirement["topic"]
        )
        level_matches = (
            search_requirement["level"] is None
            or resource.difficulty == search_requirement["level"]
        )

        if topic_matches and level_matches:
            matches.append(resource)

    return matches