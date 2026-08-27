"""
Orchestrates retrieval with tiered fallback:
1. Exact topic + exact level match
2. Exact topic match, any level
3. Semantic (meaning-based) match -- real neural embeddings if available, else word-count fallback
4. Everything in the database (broad last resort)
5. External Resource Discovery -> Analysis -> Verification -> Store

Every tier is filtered against the learner's history. If filtering empties a
tier, the next tier runs -- and an exhausted learner therefore falls through
to discovery, where query variation finds genuinely new material.
"""

from src.agents.recommendation_system.database.resource_store import retrieve_from_database, get_all_resources, add_resources
from src.agents.recommendation_system.retrieval.discover import discover_resources
from src.agents.recommendation_system.analysis.resource_analyzer import analyze_resources
from src.agents.recommendation_system.verification.verifier import verify_resources

SIMILARITY_THRESHOLD = 0.5

# Discovery targets resources that SURVIVE verification, not raw candidates.
# Real runs showed candidates being lost to dead links and blocked domains,
# which left the learner with a single recommendation.
#
# We deliberately fetch far more candidates than the learner needs. Every
# verified resource is saved to the shared catalog, so the surplus becomes
# stock for FUTURE requests -- from this learner or any other. A later
# request for the same topic is then answered from tier 1 with no network
# calls at all. The learner still receives only TARGET_VERIFIED_RESOURCES,
# ranked against their own preferences.
TARGET_VERIFIED_RESOURCES = 5
CANDIDATES_PER_ROUND = 15
MAX_DISCOVERY_ROUNDS = 3

try:
    from src.agents.recommendation_system.retrieval.embeddings import neural_cosine_similarity
    neural_cosine_similarity("warm-up check", "confirms the model loads")
    similarity_function = neural_cosine_similarity
    print("[semantic retrieval] Using real neural embeddings.")
except Exception as error:
    from src.agents.recommendation_system.retrieval.semantic import cosine_similarity
    similarity_function = cosine_similarity
    print(f"[semantic retrieval] Neural embeddings unavailable ({error}); falling back to word-count similarity.")


def exclude_seen(resources, seen_urls):
    """Drops resources this learner has already encountered."""
    if not seen_urls:
        return resources
    return [resource for resource in resources if resource.url not in seen_urls]


def semantic_retrieve(search_requirement):
    """Tier 3: meaning-based matching against the whole catalog."""
    topic = search_requirement["topic"]
    if topic is None:
        return []

    scored_resources = []
    for resource in get_all_resources():
        resource_text = resource.topic + " " + resource.description
        similarity = similarity_function(topic, resource_text)
        if similarity >= SIMILARITY_THRESHOLD:
            scored_resources.append((similarity, resource))

    scored_resources.sort(key=lambda pair: pair[0], reverse=True)
    return [resource for similarity, resource in scored_resources]


def discover_and_store(search_requirement, exclude_urls=None, target=TARGET_VERIFIED_RESOURCES):
    """Tier 5: search the real internet until enough resources SURVIVE
    verification, then Analyze -> Verify -> Store.

    Runs in rounds. Each round asks discovery for more candidates, excluding
    everything already tried, and keeps whatever passes verification. Stops
    when the target is met, when a round finds no new candidates at all, or
    when MAX_DISCOVERY_ROUNDS is reached -- so a topic with little good
    material fails in bounded time rather than searching forever.

    Everything verified is saved; only `target` is returned.
    """
    if exclude_urls is None:
        exclude_urls = set()

    tried_urls = set(exclude_urls)
    verified_total = []

    for round_number in range(1, MAX_DISCOVERY_ROUNDS + 1):
        if len(verified_total) >= target:
            break

        candidates = discover_resources(
            search_requirement,
            exclude_urls=tried_urls,
            max_results=CANDIDATES_PER_ROUND,
        )

        if not candidates:
            print(f"[resource discovery] Round {round_number}: no new candidates found; stopping.")
            break

        for candidate in candidates:
            tried_urls.add(candidate.url)

        analyzed = analyze_resources(candidates)
        verified = verify_resources(analyzed, verbose=True)
        verified_total.extend(verified)

        print(
            f"[resource discovery] Round {round_number}: "
            f"{len(candidates)} candidates -> {len(verified)} verified "
            f"({len(verified_total)}/{target} needed)."
        )

    if not verified_total:
        return []

    # Save EVERYTHING verified -- each one already cost a real HTTP request,
    # and discarding it means paying to rediscover it later. The surplus goes
    # into the shared catalog so future requests find it in tier 1 for free.
    saved_count = add_resources(verified_total)
    surplus = max(0, len(verified_total) - target)
    print(
        f"[resource discovery] {len(verified_total)} verified, {saved_count} newly saved to the database "
        f"({surplus} kept in the catalog for future requests)."
    )

    return verified_total[:target]


def retrieve_with_fallback(search_requirement, seen_urls=None, target=TARGET_VERIFIED_RESOURCES):
    """Runs the tiers in order, stopping at the first that yields resources
    this learner has not already encountered.

    seen_urls is filtered out of EVERY tier. That is what makes an exhausted
    learner fall through to tier 5, where query variation searches the web
    with different phrasings and finds genuinely new material.

    target is how many resources the caller needs. It matters only for tier 5:
    a learner asking for 10 cannot be satisfied by a search that stops at 5.
    """
    if seen_urls is None:
        seen_urls = set()

    # Tier 1: exact topic AND exact level.
    resources = exclude_seen(retrieve_from_database(search_requirement), seen_urls)
    if resources:
        return resources

    # Tier 2: same topic, any level.
    relaxed_requirement = dict(search_requirement)
    relaxed_requirement["level"] = None
    resources = exclude_seen(retrieve_from_database(relaxed_requirement), seen_urls)
    if resources:
        return resources

    # Tier 3: meaning-based match.
    resources = exclude_seen(semantic_retrieve(search_requirement), seen_urls)
    if resources:
        return resources

    # Tier 4: everything we have -- ONLY when no topic was specified.
    #
    # A catch-all is right when we have no idea what the learner wants. It is
    # WRONG when they named a topic: a real run returned all 47 machine
    # learning resources to a learner who asked for calculus, because tier 4
    # matched everything and tier 5 therefore never ran.
    if search_requirement["topic"] is None:
        relaxed_requirement["topic"] = None
        resources = exclude_seen(retrieve_from_database(relaxed_requirement), seen_urls)
        if resources:
            return resources

    # Tier 5: last resort -- go out to the real internet, skipping anything
    # this learner has already been shown.
    return discover_and_store(search_requirement, exclude_urls=seen_urls, target=target)