"""
Orchestrates retrieval, including the Scenario F fallback logic of
progressively relaxing constraints when strict retrieval finds nothing.

Order of attempts, from most to least strict:
1. Exact topic + exact level match
2. Exact topic match, any level
3. Semantic (meaning-based) match on topic, any level -- real neural
   embeddings if available, otherwise our simplified word-count version
4. Everything in the database (last resort, ignores topic and level)
"""

from database.resource_store import retrieve_from_database, MOCK_RESOURCE_DATABASE

SIMILARITY_THRESHOLD = 0.2

try:
    from retrieval.embeddings import neural_cosine_similarity
    neural_cosine_similarity("warm-up check", "confirms the model loads")
    similarity_function = neural_cosine_similarity
    print("[semantic retrieval] Using real neural embeddings.")
except Exception as error:
    from retrieval.semantic import cosine_similarity
    similarity_function = cosine_similarity
    print(f"[semantic retrieval] Neural embeddings unavailable ({error}); falling back to word-count similarity.")


def semantic_retrieve(search_requirement):
    """
    Compares the learner's goal against every resource's topic + description
    using cosine similarity, and keeps anything reasonably similar, even if
    no exact words matched.

    Args:
        search_requirement (dict): output of build_search_requirement().

    Returns:
        list: Resource objects with similarity above SIMILARITY_THRESHOLD,
              most similar first.
    """
    topic = search_requirement["topic"]

    if topic is None:
        return []

    scored_resources = []

    for resource in MOCK_RESOURCE_DATABASE:
        resource_text = resource.topic + " " + resource.description
        similarity = similarity_function(topic, resource_text)

        if similarity >= SIMILARITY_THRESHOLD:
            scored_resources.append((similarity, resource))

    scored_resources.sort(key=lambda pair: pair[0], reverse=True)

    return [resource for similarity, resource in scored_resources]


def retrieve_with_fallback(search_requirement):
    """
    Tries retrieval strategies from most to least strict, stopping as soon
    as one of them finds something.

    Scenario E note: if every strategy here finds nothing, the full target
    architecture would now hand off to external Resource Discovery
    (Section 11-14). That path is not built yet -- this function is the
    exact hook where it will plug in later.

    Args:
        search_requirement (dict): output of build_search_requirement().

    Returns:
        list: resource objects, possibly empty.
    """
    resources = retrieve_from_database(search_requirement)

    if resources:
        return resources

    relaxed_requirement = dict(search_requirement)
    relaxed_requirement["level"] = None
    resources = retrieve_from_database(relaxed_requirement)

    if resources:
        return resources

    resources = semantic_retrieve(search_requirement)

    if resources:
        return resources

    relaxed_requirement["topic"] = None
    resources = retrieve_from_database(relaxed_requirement)

    return resources