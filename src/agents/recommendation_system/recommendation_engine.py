"""
Team Beta - Recommendation Engine
Step 1: Mock Digital Twin Interface
Step 2: Search Requirement Builder
Step 3: Basic Resource Retrieval (placeholder database, topic/level filtering only)
Step 4: Verification Gate (placeholder - structural checks only, no real URL check yet)
Step 5: Code-Based Scoring & Ranking
Step 6: Decision Record & Explainability
Step 7: Fallback Architecture (covers all Section 16 scenarios A-I)

This file will grow one component at a time.
"""


def get_relevant_digital_twin_state():
    """
    This function stands in for Team Alpha's real Digital Twin.

    Right now it just returns a hardcoded dictionary. Later, this function's
    INSIDE can be replaced with a real database call or API call to Team
    Alpha's system -- and nothing else in our Recommendation Engine will
    need to change, because every other component only ever calls this
    function, never reaches into the Digital Twin directly.

    Returns:
        dict: a dictionary describing what we currently know about the learner.
    """
    learner_state = {
        "level": "beginner",
        "goal": "machine learning",
        "preferred_format": "video",
        "preferred_duration": "short",
    }

    return learner_state


def build_search_requirement(learner):
    """
    Turns learner information into a plain description of what to search for.

    This function does NOT search anything. It does NOT decide which resource
    is good. Its only job is to translate learner data into search terms.

    Args:
        learner (dict): the learner state, e.g. what get_relevant_digital_twin_state() returns.

    Returns:
        dict: a smaller dictionary describing what kind of resource to look for.
    """
    search_requirement = {
        "topic": learner["goal"],
        "level": learner["level"],
    }

    return search_requirement


MOCK_RESOURCE_DATABASE = [
    {
        "title": "Machine Learning for Absolute Beginners",
        "url": "https://example.com/ml-beginners-video",
        "description": "A short beginner-friendly video introduction to machine learning.",
        "topic": "machine learning",
        "difficulty": "beginner",
        "format": "video",
        "duration": "short",
    },
    {
        "title": "Deep Learning Specialization",
        "url": "https://example.com/deep-learning-course",
        "description": "A long, in-depth advanced course on deep learning.",
        "topic": "machine learning",
        "difficulty": "advanced",
        "format": "video",
        "duration": "long",
    },
    {
        "title": "Introduction to Data Structures",
        "url": "https://example.com/data-structures-article",
        "description": "A beginner article about data structures.",
        "topic": "data structures",
        "difficulty": "beginner",
        "format": "article",
        "duration": "short",
    },
]


KNOWN_LEVELS = ["beginner", "intermediate", "advanced"]
KNOWN_FORMATS = ["video", "article", "course", "book", "tutorial", "documentation"]
KNOWN_DURATIONS = ["short", "medium", "long"]

FIELD_ALIASES = {
    "level": ["level", "current_skill_level", "skill_level"],
    "goal": ["goal", "learning_goal", "objective"],
    "preferred_format": ["preferred_format", "format_preference"],
    "preferred_duration": ["preferred_duration", "duration_preference"],
}


def normalize_learner_state(raw_learner):
    """
    Adapter layer between whatever the real Digital Twin sends us and the
    clean, predictable shape the rest of our system expects.

    Handles:
    - Scenario A (no data at all): raw_learner may be None or empty -- we
      never crash, we just end up with all fields set to None.
    - Scenario C (different field names): the Digital Twin might call the
      level field "current_skill_level" instead of "level" -- FIELD_ALIASES
      lets us recognize either name.
    - Scenario D (invalid/unexpected values): a value we don't recognize
      (e.g. "intermediate-beginner") is treated as unknown (None) instead of
      guessed at.

    We deliberately do NOT invent values here (Scenario B) -- if something
    is missing, it stays None, and later code must handle that explicitly.

    Args:
        raw_learner (dict or None): whatever the Digital Twin gave us.

    Returns:
        dict: normalized learner state with keys level, goal,
              preferred_format, preferred_duration -- each either a real
              value or None.
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

    # Scenario D: reject unrecognized values instead of trusting them blindly.
    if normalized["level"] not in KNOWN_LEVELS:
        normalized["level"] = None

    if normalized["preferred_format"] not in KNOWN_FORMATS:
        normalized["preferred_format"] = None

    if normalized["preferred_duration"] not in KNOWN_DURATIONS:
        normalized["preferred_duration"] = None

    # "goal" is free text (not a fixed category), so we leave it as-is,
    # even if it's None.

    return normalized


def retrieve_from_database(search_requirement):
    """
    Looks through our mock resource database and returns resources whose
    topic and difficulty level match the search requirement.

    Scenario A/B support: if the search requirement doesn't specify a topic
    or level (because the learner data didn't have one), we don't filter on
    that field at all, instead of crashing or wrongly excluding everything.

    This function does NOT decide which resource is best. It only filters
    down to resources worth considering further.

    Args:
        search_requirement (dict): output of build_search_requirement().

    Returns:
        list: a list of resource dictionaries that match the topic and level.
    """
    matches = []

    for resource in MOCK_RESOURCE_DATABASE:
        topic_matches = (
            search_requirement["topic"] is None
            or resource["topic"] == search_requirement["topic"]
        )
        level_matches = (
            search_requirement["level"] is None
            or resource["difficulty"] == search_requirement["level"]
        )

        if topic_matches and level_matches:
            matches.append(resource)

    return matches


def retrieve_with_fallback(search_requirement):
    """
    Scenario F: if strict retrieval finds nothing, progressively relax
    constraints and try again, instead of giving up immediately.

    Order of relaxation: first drop the level requirement (less critical),
    then drop the topic requirement too (last resort, broadest possible
    search). This mirrors your document's "broaden the search, relax
    non-critical constraints" guidance.

    Scenario E note: if this still returns nothing, in the full target
    architecture we would now hand off to the Resource Discovery / Resource
    Analysis / Verification path (Section 11-14) to search externally. That
    external discovery path is not built yet in this file -- this function
    is the exact hook where it will plug in later.

    Args:
        search_requirement (dict): output of build_search_requirement().

    Returns:
        list: resource dictionaries, possibly empty if nothing at all matches.
    """
    resources = retrieve_from_database(search_requirement)

    if resources:
        return resources

    relaxed_requirement = dict(search_requirement)
    relaxed_requirement["level"] = None
    resources = retrieve_from_database(relaxed_requirement)

    if resources:
        return resources

    relaxed_requirement["topic"] = None
    resources = retrieve_from_database(relaxed_requirement)

    return resources


def calculate_confidence(learner):
    """
    Scenario H/I: measures how much of the learner's profile was actually
    available to personalize against. This stops the system from silently
    pretending a recommendation is fully personalized when it isn't.

    Args:
        learner (dict): normalized learner state.

    Returns:
        float: a number from 0.0 (nothing known) to 1.0 (everything known).
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


def build_score_breakdown(learner, resource):
    """
    Compares each preference individually and returns a breakdown showing how
    many points came from each factor. This is the raw material that both the
    total score AND the human-readable reasons are built from.

    Scenario B/D safety: a factor only earns points if the learner's value is
    known AND matches. If the learner's preference is None (unknown), that
    factor contributes 0 -- we never guess a match for missing data.

    Args:
        learner (dict): the learner state.
        resource (dict): a single verified resource.

    Returns:
        dict: points earned per factor, e.g. {"format_match": 30, "level_match": 0, ...}
    """
    breakdown = {
        "format_match": 30 if learner["preferred_format"] is not None and learner["preferred_format"] == resource["format"] else 0,
        "level_match": 30 if learner["level"] is not None and learner["level"] == resource["difficulty"] else 0,
        "duration_match": 20 if learner["preferred_duration"] is not None and learner["preferred_duration"] == resource["duration"] else 0,
        "goal_relevance": 20 if learner["goal"] is not None and learner["goal"] == resource["topic"] else 0,
    }

    return breakdown


def verify_resource(resource):
    """
    Checks whether a resource is well-formed enough to be recommended.

    PLACEHOLDER VERSION: this only checks that the required fields exist and
    are not empty. It does NOT yet check whether the URL is actually reachable
    on the internet -- that requires a real network request, which we'll add
    later using the `requests` library once you're running this on your own
    machine with normal internet access.

    Args:
        resource (dict): a candidate resource, e.g. one item from retrieve_from_database().

    Returns:
        bool: True if the resource passes our current checks, False otherwise.
    """
    has_title = bool(resource.get("title"))
    has_url = bool(resource.get("url"))
    has_topic = bool(resource.get("topic"))

    return has_title and has_url and has_topic


def verify_resources(resources):
    """
    Runs verify_resource() over a list of candidate resources and keeps only
    the ones that pass.

    Args:
        resources (list): list of candidate resource dictionaries.

    Returns:
        list: only the resources that passed verification.
    """
    verified = []

    for resource in resources:
        if verify_resource(resource):
            verified.append(resource)

    return verified


def calculate_score(learner, resource):
    """
    Calculates a numeric fit score for one resource, based on the learner's
    preferences. This is 100% code-based -- no LLM involved -- so the same
    inputs always produce the exact same score. That's what makes it
    reproducible.

    Args:
        learner (dict): the learner state.
        resource (dict): a single verified resource.

    Returns:
        int: a score from 0 to 100.
    """
    breakdown = build_score_breakdown(learner, resource)

    return sum(breakdown.values())


def create_decision_record(learner, resource):
    """
    Builds a structured explanation of why a resource received its score.
    The reasons list is generated directly from the breakdown -- never
    invented by an LLM -- so every reason is traceable back to a real
    comparison between learner and resource.

    Scenario H/I: also includes a personalization_confidence value, so the
    system never silently pretends a low-data recommendation is fully
    personalized.

    Args:
        learner (dict): the learner state.
        resource (dict): a single verified resource.

    Returns:
        dict: {"resource": ..., "score": ..., "score_breakdown": ...,
               "reasons": [...], "personalization_confidence": ...}
    """
    breakdown = build_score_breakdown(learner, resource)
    score = sum(breakdown.values())
    confidence = calculate_confidence(learner)

    reasons = []

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
        "resource": resource["title"],
        "score": score,
        "score_breakdown": breakdown,
        "reasons": reasons,
        "personalization_confidence": confidence,
    }

    return decision_record


def recommend(learner, resources):
    """
    Builds a decision record for every verified resource and returns them
    ranked from best to worst.

    Args:
        learner (dict): the learner state.
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


def get_recommendations(raw_learner):
    """
    The full pipeline, start to finish, with fallback handling built in at
    every stage. This function is safe to call with messy, partial, or even
    completely empty learner data -- it will never crash.

    Args:
        raw_learner (dict or None): raw learner data, in any schema.

    Returns:
        dict: {"recommendations": [...], "message": ...}
              "message" explains what happened if no resources were found.
    """
    learner = normalize_learner_state(raw_learner)
    search_requirement = build_search_requirement(learner)
    resources = retrieve_with_fallback(search_requirement)
    verified_resources = verify_resources(resources)

    if not verified_resources:
        # Scenario E/G: nothing survived, and we have no discovery path yet.
        return {
            "recommendations": [],
            "message": "No suitable verified resources were found for this learner.",
        }

    recommendations = recommend(learner, verified_resources)

    return {
        "recommendations": recommendations,
        "message": "OK",
    }


# A few deliberately messy example inputs, one per scenario from Section 16,
# used below to prove the pipeline doesn't crash on any of them.
SCENARIO_EXAMPLES = {
    "A - no data at all": None,
    "B - partial data": {"goal": "machine learning"},
    "C - different field names": {
        "current_skill_level": "beginner",
        "learning_goal": "machine learning",
        "format_preference": "video",
        "duration_preference": "short",
    },
    "D - invalid values": {
        "level": "intermediate-beginner",
        "goal": "machine learning",
        "preferred_format": None,
        "preferred_duration": "short",
    },
}


if __name__ == "__main__":
    # This block only runs when we execute this file directly (not when it's
    # imported by another file later). It's how we manually test our function.

    print("=== Normal case (clean Digital Twin data) ===")
    learner = get_relevant_digital_twin_state()
    result = get_recommendations(learner)
    for record in result["recommendations"]:
        print(f"\nResource: {record['resource']}")
        print(f"Score: {record['score']}")
        print(f"Confidence: {record['personalization_confidence']}")
        print(f"Reasons: {record['reasons']}")

    for scenario_name, raw_learner in SCENARIO_EXAMPLES.items():
        print(f"\n=== Scenario {scenario_name} ===")
        print(f"Raw input: {raw_learner}")

        normalized = normalize_learner_state(raw_learner)
        print(f"Normalized: {normalized}")

        result = get_recommendations(raw_learner)
        print(f"Message: {result['message']}")

        for record in result["recommendations"]:
            print(f"Resource: {record['resource']} | Score: {record['score']} | Confidence: {record['personalization_confidence']}")