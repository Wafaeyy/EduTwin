"""
Team Beta - Recommendation Engine
Main pipeline: wires every module together.
"""

from src.agents.recommendation_system.twin.mock_twin import get_relevant_digital_twin_state, normalize_learner_state
from src.agents.recommendation_system.twin.request_extractor import extract_request
from src.agents.recommendation_system.retrieval.search_requirement import build_search_requirement
from src.agents.recommendation_system.retrieval.retriever import retrieve_with_fallback
from src.agents.recommendation_system.verification.verifier import verify_resources
from src.agents.recommendation_system.recommendation.engine import recommend
from src.agents.recommendation_system.analysis.resource_analyzer import infer_format_from_url
from src.agents.recommendation_system.analysis.video_content_analyzer import analyze_video_content
from src.agents.recommendation_system.analysis.article_content_analyzer import analyze_article_content
from src.agents.recommendation_system.database.persistence import (
    get_seen_urls,
    record_shown,
    record_rejected,
    EVENT_REJECTED,
    save_analysis,
    load_analysis,
)

# How many resources the learner receives when they do not ask for a specific
# number.
#
# Tier 1 returns EVERYTHING matching, and the catalogue grows with every
# discovery run -- real runs returned 12 and then 26 resources, which is a
# search results page, not a recommendation.
#
# Capping also protects the history. Only what the learner SAW may be recorded
# as shown; recording 26 when they saw 5 would wrongly exclude 21 good
# resources from every future request.
MAX_RECOMMENDATIONS = 5

# Resources scoring below this are not shown. A weak match is worse than an
# honest "nothing good found" -- it wastes the learner's time and makes the
# engine look careless.
#
# If NOTHING clears the bar, the best available are returned anyway with a
# message saying so: never return nothing when something exists, but never
# present a weak match as though it were a good one either.
MIN_RECOMMENDATION_SCORE = 50


def apply_request(learner, user_request):
    """Overlays what the learner asked for RIGHT NOW onto their stored state.

    The rule: THE REQUEST WINS, MEMORY FILLS THE GAPS.

    A learner whose stored goal is "artificial intelligence" can still ask
    about calculus today, and the engine must search for calculus. But if they
    just say "recommend something", their stored goal and preferences are
    exactly what should be used.

    Returns (learner, notes, requested_count). requested_count is None unless
    the learner asked for a specific number, in which case the caller uses it
    instead of the default limit.
    """
    notes = []
    requested_count = None

    if not user_request or not user_request.strip():
        return learner, notes, requested_count

    requested = extract_request(user_request)
    if not requested:
        return learner, notes, requested_count

    # topic -> goal. The most important override: it decides what we search
    # for, and it drives the topic gate in the scorer.
    if requested.get("topic"):
        if learner.get("goal") and requested["topic"] != learner["goal"]:
            notes.append(
                f"Searching for '{requested['topic']}' as requested, "
                f"rather than the stored goal '{learner['goal']}'."
            )
        learner["goal"] = requested["topic"]

    if requested.get("format"):
        learner["preferred_format"] = requested["format"]

    if requested.get("level"):
        learner["level"] = requested["level"]

    if requested.get("duration"):
        learner["preferred_duration"] = requested["duration"]

    requested_count = requested.get("count")

    return learner, notes, requested_count


def load_history(twin_id, exclude_seen_resources):
    """Returns the urls to exclude for this learner.

    Rejections are ALWAYS excluded -- a learner who refused something should
    never see it again. Merely-shown resources are excluded only when the
    caller asks (i.e. the learner said "recommend something else"), so that
    repeating the same question still gives the same reproducible answer.
    """
    if not twin_id:
        return set()

    try:
        if exclude_seen_resources:
            return get_seen_urls(twin_id)
        return get_seen_urls(twin_id, events=[EVENT_REJECTED])
    except Exception as error:
        print(f"[history] Could not load learner history ({error}); proceeding without exclusions.")
        return set()


def save_history(twin_id, recommendations):
    """Records what we just showed, so it can be excluded next time.

    Must be called with the FINAL, capped list. Recording resources the
    learner never saw would silently exclude them from future requests.
    """
    if not twin_id or not recommendations:
        return

    urls = [record["url"] for record in recommendations]
    try:
        record_shown(twin_id, urls)
    except Exception as error:
        print(f"[history] Could not record shown resources ({error}); continuing.")


def get_recommendations(raw_learner, exclude_seen_resources=False, limit=MAX_RECOMMENDATIONS,
                        user_request=None):
    """Full pipeline.

    user_request is what the learner typed. Anything it explicitly asks for
    overrides the stored Digital Twin state -- including HOW MANY resources
    they want. "Give me 10 videos about python" returns up to 10, not 5.

    Asking for 10 does not guarantee 10: only resources that pass the topic
    gate and clear MIN_RECOMMENDATION_SCORE are returned. Padding the list
    with weak matches would defeat the filter.

    Set exclude_seen_resources=True when the learner asks for DIFFERENT
    resources than they were given before.
    """
    learner = normalize_learner_state(raw_learner)
    twin_id = learner.get("twin_id")

    learner, request_notes, requested_count = apply_request(learner, user_request)

    # The learner's own number wins over the default.
    if requested_count:
        limit = requested_count
        print(f"[recommendation] Learner asked for {requested_count}; returning up to that many.")

    seen_urls = load_history(twin_id, exclude_seen_resources)
    if seen_urls:
        print(f"[history] Excluding {len(seen_urls)} resource(s) already seen by this learner.")

    search_requirement = build_search_requirement(learner)

    # Discovery must find at least as many as the learner asked for, or a
    # request for 10 could never be satisfied from a five-resource search.
    resources = retrieve_with_fallback(search_requirement, seen_urls=seen_urls, target=limit)
    verified_resources = verify_resources(resources)

    if not verified_resources:
        return {
            "recommendations": [],
            "message": "No new resources were found for this learner. They may have seen everything available on this topic.",
            "notes": request_notes,
        }

    ranked = recommend(learner, verified_resources)

    # Drop weak matches. Off-topic resources score 0 via the scorer's topic
    # gate, so this is what actually removes them from the learner's view.
    strong = [record for record in ranked if record["score"] >= MIN_RECOMMENDATION_SCORE]

    if strong:
        recommendations = strong[:limit]
        message = "OK"
        if len(strong) < len(ranked):
            dropped = len(ranked) - len(strong)
            print(f"[recommendation] Dropped {dropped} resource(s) scoring below {MIN_RECOMMENDATION_SCORE}.")
        if requested_count and len(recommendations) < requested_count:
            message = (
                f"Only {len(recommendations)} strong match(es) were found, "
                f"fewer than the {requested_count} requested."
            )
    else:
        # Nothing cleared the bar. Return the best available rather than
        # nothing, but say plainly that these are weak matches.
        recommendations = ranked[:limit]
        message = (
            f"No strong matches were found. These are the closest available, "
            f"but none scored {MIN_RECOMMENDATION_SCORE} or above."
        )
        print(f"[recommendation] Nothing reached {MIN_RECOMMENDATION_SCORE}; returning the best available.")

    if len(ranked) > len(recommendations):
        print(f"[recommendation] {len(ranked)} matched; returning {len(recommendations)}.")

    # Cap and filter happen BEFORE recording history -- see save_history().
    save_history(twin_id, recommendations)

    return {"recommendations": recommendations, "message": message, "notes": request_notes}


def reject_recommendations(raw_learner, resource_urls):
    """Records that the learner does not want these resources. They will
    never be recommended to this learner again."""
    learner = normalize_learner_state(raw_learner)
    twin_id = learner.get("twin_id")
    if not twin_id:
        return 0
    try:
        return record_rejected(twin_id, resource_urls)
    except Exception as error:
        print(f"[history] Could not record rejections ({error}).")
        return 0


CONTENT_ANALYZABLE_FORMATS = {"video", "article", "research_paper"}


def analyze_single_resource(resource_url, resource_format=None, topic=None, use_cache=True):
    """Deep content analysis of ONE resource the learner explicitly picked.

    This is what the "What's inside?" button calls. It works on ANY resource
    url, not just the top-ranked one, so the learner chooses what to look into.

    Checks the shared cache first: an analysis paid for by ANY learner is
    reused by every other learner, and a cached hit costs no Gemini call at
    all -- which also means it still works when Gemini is overloaded.

    Only successful analyses are cached. A failure (blocked transcript, API
    outage) is returned but never stored, so a temporary problem does not
    permanently poison the resource.
    """
    if not resource_url:
        return {"access_status": "No resource_url was provided."}

    if use_cache:
        try:
            cached = load_analysis(resource_url)
            if cached is not None:
                print(f"[analysis cache] Hit for {resource_url} -- no Gemini call needed.")
                return cached
        except Exception as error:
            print(f"[analysis cache] Could not read cache ({error}); analyzing fresh.")

    # The Orchestrator may not know the format of a url the learner pasted in.
    if resource_format is None:
        resource_format = infer_format_from_url(resource_url)

    # A playlist is many videos, so it has no single transcript to analyse.
    if resource_format == "playlist":
        return {"access_status": "This is a playlist of many videos, not a single video, so it cannot be analysed."}

    if resource_format == "video":
        analysis = analyze_video_content(resource_url)
        analysis_type = "video"
    elif resource_format in CONTENT_ANALYZABLE_FORMATS or resource_format is None:
        # Unknown format falls through to article analysis: most web pages are
        # readable text, so attempting it beats refusing outright.
        analysis = analyze_article_content(resource_url, topic=topic)
        analysis_type = "article"
    else:
        return {"access_status": f"Deep content analysis is not yet supported for format '{resource_format}'."}

    # Cache only genuine successes.
    if analysis.get("access_status") == "ok":
        try:
            save_analysis(resource_url, analysis_type, analysis)
            print(f"[analysis cache] Stored analysis for {resource_url}.")
        except Exception as error:
            print(f"[analysis cache] Could not store analysis ({error}); continuing.")

    return analysis


def get_recommendation_with_content(raw_learner, exclude_seen_resources=False,
                                    limit=MAX_RECOMMENDATIONS, user_request=None):
    """
    Runs the full recommendation pipeline, then analyses ONLY the top-ranked
    resource.

    Mostly superseded by analyze_single_resource(), which lets the learner
    pick which resource to look into. Kept for interfaces without buttons.
    """
    result = get_recommendations(
        raw_learner,
        exclude_seen_resources=exclude_seen_resources,
        limit=limit,
        user_request=user_request,
    )

    if not result["recommendations"]:
        result["top_resource_content"] = None
        return result

    top_recommendation = result["recommendations"][0]

    # Analyse against the topic actually searched for, which may be the
    # request's topic rather than the stored goal.
    learner = normalize_learner_state(raw_learner)
    learner, _, _ = apply_request(learner, user_request)

    result["top_resource_content"] = analyze_single_resource(
        top_recommendation["url"],
        top_recommendation["format"],
        topic=learner.get("goal"),
    )
    return result


def format_score_breakdown(breakdown):
    """Turns the breakdown dict into a compact one-line summary."""
    return (
        f"format {breakdown['format_match']} | "
        f"level {breakdown['level_match']} | "
        f"duration {breakdown['duration_match']} | "
        f"goal {breakdown['goal_relevance']}"
    )


def print_recommendation(record, detailed=True):
    """Prints one decision record. Detailed mode shows reasons and breakdown."""
    print(f"\n  {record['resource']}")
    print(f"    URL:        {record['url']}")
    print(f"    Format:     {record['format']}")
    print(f"    Score:      {record['score']}/100   ({format_score_breakdown(record['score_breakdown'])})")
    print(f"    Confidence: {record['personalization_confidence']}")
    if detailed:
        for reason in record["reasons"]:
            print(f"    - {reason}")


if __name__ == "__main__":
    learner = get_relevant_digital_twin_state()
    print(f"Stored Twin state: goal={learner['goal']!r}, format={learner['preferred_format']!r}, "
          f"level={learner['level']!r}, duration={learner['preferred_duration']!r}")

    print("\n\n=== 1. No request -- uses the stored goal, default of 5 ===")
    result = get_recommendations(learner)
    print(f"Message: {result['message']}")
    print(f"Returned {len(result['recommendations'])} resource(s).  <- should be 5 or fewer")
    for record in result["recommendations"]:
        print_recommendation(record, detailed=False)

    print("\n\n=== 2. Learner asks for a SPECIFIC NUMBER ===")
    result = get_recommendations(learner, user_request="give me 8 videos about machine learning")
    print(f"Message: {result['message']}")
    print(f"Returned {len(result['recommendations'])} resource(s).  <- should be up to 8")
    for record in result["recommendations"]:
        print(f"  {record['score']:>3} | {record['url']}")

    print("\n\n=== 3. Request names a COMPLETELY different topic ===")
    print("Off-topic resources must score 0 and be dropped, forcing discovery.")
    result = get_recommendations(learner, user_request="recommend 3 videos about calculus")
    print(f"Notes: {result['notes']}")
    print(f"Message: {result['message']}")
    print(f"Returned {len(result['recommendations'])} resource(s).  <- should be up to 3")
    for record in result["recommendations"]:
        print_recommendation(record, detailed=True)

    print("\n\n=== 4. Vague request -- falls back to stored state and default ===")
    result = get_recommendations(learner, user_request="recommend something for me")
    print(f"Notes: {result['notes']}  <- should be empty")
    print(f"Returned {len(result['recommendations'])} resource(s).")