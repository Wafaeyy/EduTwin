"""
External Resource Discovery (Section 11): searches the real internet for
candidate resources when our database has nothing suitable, instead of only
ever being limited to our fixed mock catalog.

The search query is built based on the learner's preferred format, so we
don't accidentally bias every search toward one content type (e.g. always
searching for "tutorial" would miss books, research papers, courses, and
practice/problem-solving platforms like LeetCode). If no format is known,
we search neutrally, so results naturally come back as a mix of types.

HONEST NOTE #2: search results only tell us a page's title, link, and a
short snippet -- they do NOT reliably tell us the resource's real format,
difficulty, or duration. Rather than guess and risk a false match, we leave
those fields as None (unknown), EXCEPT format, which we set to whatever the
learner asked for, since that's literally what we searched for.

"""

from ddgs import DDGS
from models.resource import Resource

MAX_DISCOVERY_RESULTS = 5

FORMAT_SEARCH_TERMS = {
    "video": "video",
    "article": "article",
    "course": "online course",
    "book": "book",
    "tutorial": "tutorial",
    "documentation": "official documentation",
    "research_paper": "research paper",
    "practice_platform": "practice problems",
}


def build_discovery_query(search_requirement):
    """
    Turns a search requirement into a plain text search engine query.

    If a format is specified, the query is built around that format
    specifically. If not, the query stays neutral, so results come back as
    a natural mix of whatever content types exist for the topic.

    Args:
        search_requirement (dict): output of build_search_requirement().

    Returns:
        str: a search query string.
    """
    topic = search_requirement["topic"] or ""
    level = search_requirement["level"] or ""
    requested_format = search_requirement.get("format")

    format_term = FORMAT_SEARCH_TERMS.get(requested_format, "")

    query = f"{topic} {level} {format_term}".strip()
    query = " ".join(query.split())

    return query


def discover_resources(search_requirement):
    """
    Searches the real internet for candidate resources matching the topic.

    Args:
        search_requirement (dict): output of build_search_requirement().

    Returns:
        list: Resource objects built from real search results. difficulty
              and duration are left as None (unknown), since we cannot
              verify them from a search snippet alone. format is set to
              whatever was requested, since that's what we searched for.
    """
    topic = search_requirement["topic"]

    if topic is None:
        return []

    query = build_discovery_query(search_requirement)
    requested_format = search_requirement.get("format")
    discovered = []

    try:
        with DDGS() as search_engine:
            results = search_engine.text(query, max_results=MAX_DISCOVERY_RESULTS)

            for result in results:
                resource = Resource(
                    title=result.get("title", ""),
                    url=result.get("href", ""),
                    description=result.get("body", ""),
                    topic=topic,
                    difficulty=None,
                    format=requested_format,
                    duration=None,
                )
                discovered.append(resource)
    except Exception as error:
        print(f"[resource discovery] Search failed ({error}); returning no discovered resources.")
        return []

    return discovered