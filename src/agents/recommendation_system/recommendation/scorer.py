"""
Code-based scoring: format 30 / level 30 / duration 20 / goal 20 = 100 max.
Also computes personalization_confidence.

TOPIC GATE: when the learner has named a topic, a resource that is not
genuinely about that topic scores ZERO, whatever else it matches. A machine
learning video is not a useful answer to "recommend videos about calculus"
just because the format happens to be right -- and a real run returned exactly
that, at 30/100, purely on the format match.

Relevance is judged semantically, not by string equality. A resource stored
under "machine learning" should still count for a request about "machine
learning basics"; exact matching would throw away almost the whole catalogue
and force a web search on nearly every request.
"""

from src.agents.recommendation_system.retrieval.retriever import similarity_function

# How semantically close a resource's topic must be to what the learner asked
# for. Above this it counts as being about that topic; below, the resource
# scores zero and is dropped.
TOPIC_RELEVANCE_THRESHOLD = 0.55


def is_topic_relevant(learner_goal, resource):
    """True if this resource is genuinely about what the learner asked for.

    Exact match first -- free, and always correct when it hits. Then semantic
    similarity for the near-misses: "machine learning basics" vs "machine
    learning", "calc 2" vs "calculus".
    """
    if not learner_goal:
        # No topic named -- nothing to be off-topic from, so the gate is open.
        return True

    if resource.topic and resource.topic.lower() == learner_goal.lower():
        return True

    resource_text = f"{resource.topic or ''} {resource.title or ''}".strip()
    if not resource_text:
        return False

    try:
        similarity = similarity_function(learner_goal, resource_text)
    except Exception:
        # If similarity cannot be computed, do not silently drop the resource.
        # Failing open is the safer direction: a weak match scores low anyway,
        # while a wrongly dropped resource disappears with no explanation.
        return True

    return similarity >= TOPIC_RELEVANCE_THRESHOLD


def build_score_breakdown(learner, resource):
    """Points per factor.

    A factor only earns points if the learner's value is KNOWN and matches --
    it never guesses a match for missing data.
    """
    breakdown = {
        "format_match": 30 if learner["preferred_format"] is not None and learner["preferred_format"] == resource.format else 0,
        "level_match": 30 if learner["level"] is not None and learner["level"] == resource.difficulty else 0,
        "duration_match": 20 if learner["preferred_duration"] is not None and learner["preferred_duration"] == resource.duration else 0,
        "goal_relevance": 20 if learner["goal"] is not None and is_topic_relevant(learner["goal"], resource) else 0,
    }
    return breakdown


def calculate_score(learner, resource):
    """Total score, with the topic gate applied.

    If the learner named a topic and this resource is not about it, the score
    is zero -- not merely lower. Whatever else it matches is irrelevant.
    """
    breakdown = build_score_breakdown(learner, resource)

    if learner["goal"] is not None and breakdown["goal_relevance"] == 0:
        return 0

    return sum(breakdown.values())


def calculate_confidence(learner):
    """How much of the learner's profile was actually known, 0.0 to 1.0.

    Lets a low score caused by an unknown profile be told apart from a low
    score caused by a genuinely poor match.
    """
    fields = [learner["level"], learner["goal"], learner["preferred_format"], learner["preferred_duration"]]
    known_count = 0
    for field in fields:
        if field is not None:
            known_count += 1
    confidence = known_count / len(fields)
    return confidence