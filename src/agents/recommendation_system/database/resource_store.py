"""
The (mocked) verified resource catalog and the code that queries it.

Later, MOCK_RESOURCE_DATABASE gets replaced by a real database. Nothing
outside this module should ever touch the raw data directly -- everything
goes through retrieve_from_database().

NOTE: URLs here are real, live pages (mostly Wikipedia, for stability) so
the real network-based Verification Gate has something genuine to check.
"Broken Link Example" deliberately points to a URL that does not exist, to
prove the Verification Gate correctly rejects it. Several formats are
represented (video, book, research paper, practice platform, article) to
show the engine isn't limited to any single content type.
"""

from models.resource import Resource

MOCK_RESOURCE_DATABASE = [
    Resource(
        title="Machine Learning for Absolute Beginners",
        url="https://en.wikipedia.org/wiki/Machine_learning",
        description="A short beginner-friendly video introduction to machine learning.",
        topic="machine learning",
        difficulty="beginner",
        format="video",
        duration="short",
    ),
    Resource(
        title="Deep Learning Specialization",
        url="https://en.wikipedia.org/wiki/Deep_learning",
        description="A long, in-depth advanced course on deep learning.",
        topic="machine learning",
        difficulty="advanced",
        format="video",
        duration="long",
    ),
    Resource(
        title="Introduction to Data Structures",
        url="https://en.wikipedia.org/wiki/Data_structure",
        description="A beginner article about data structures.",
        topic="data structures",
        difficulty="beginner",
        format="article",
        duration="short",
    ),
    Resource(
        title="Pattern Recognition and Machine Learning (textbook)",
        url="https://en.wikipedia.org/wiki/Pattern_recognition",
        description="A foundational machine learning textbook covering statistical pattern recognition.",
        topic="machine learning",
        difficulty="advanced",
        format="book",
        duration="long",
    ),
    Resource(
        title="Attention Is All You Need (research paper)",
        url="https://en.wikipedia.org/wiki/Attention_(machine_learning)",
        description="The paper introducing the transformer architecture, foundational to modern machine learning.",
        topic="machine learning",
        difficulty="advanced",
        format="research_paper",
        duration="medium",
    ),
    Resource(
        title="LeetCode - Practice Coding Problems",
        url="https://en.wikipedia.org/wiki/LeetCode",
        description="A practice platform with coding and algorithm problems, commonly used for data structures practice.",
        topic="data structures",
        difficulty="intermediate",
        format="practice_platform",
        duration="short",
    ),
    Resource(
        title="Broken Link Example",
        url="https://en.wikipedia.org/wiki/This_page_definitely_does_not_exist_xyz123",
        description="A deliberately broken URL, used to prove the Verification Gate rejects dead links.",
        topic="machine learning",
        difficulty="beginner",
        format="video",
        duration="short",
    ),
]


def retrieve_from_database(search_requirement):
    """
    Looks through the mock resource database and returns resources whose
    topic and difficulty level match the search requirement.

    If the search requirement doesn't specify a topic or level, we don't
    filter on that field at all (Scenario A/B support). Format is NOT used
    to filter here -- it's a scoring/ranking factor (Section 17), not a
    hard requirement, so resources of every format stay eligible.

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