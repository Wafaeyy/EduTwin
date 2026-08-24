"""
Team Beta - Recommendation Engine
Main pipeline: wires every module together.
"""

from src.agents.recommendation_system.twin.mock_twin import get_relevant_digital_twin_state, normalize_learner_state
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

# How many resources the learner actually receives.
#
# Tier 1 returns EVERYTHING matching, and the catalogue grows with every
# discovery run -- real runs returned 12 and then 26 resources, which is a
# search results page, not a recommendation.
#
# Capping here also protects the history. Only what the learner SAW may be
# recorded as shown; recording 26 when they saw 5 would wrongly exclude 21
# good resources from every future request.
MAX_RECOMMENDATIONS = 5


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


def get_recommendations(raw_learner, exclude_seen_resources=False, limit=MAX_RECOMMENDATIONS):
    """Full pipeline. Set exclude_seen_resources=True when the learner asks
    for DIFFERENT resources than they were given before."""
    learner = normalize_learner_state(raw_learner)
    twin_id = learner.get("twin_id")

    seen_urls = load_history(twin_id, exclude_seen_resources)
    if seen_urls:
        print(f"[history] Excluding {len(seen_urls)} resource(s) already seen by this learner.")

    search_requirement = build_search_requirement(learner)
    resources = retrieve_with_fallback(search_requirement, seen_urls=seen_urls)
    verified_resources = verify_resources(resources)

    if not verified_resources:
        return {
            "recommendations": [],
            "message": "No new resources were found for this learner. They may have seen everything available on this topic.",
        }

    ranked = recommend(learner, verified_resources)

    # Cap BEFORE recording history -- see save_history().
    recommendations = ranked[:limit]
    if len(ranked) > len(recommendations):
        print(f"[recommendation] {len(ranked)} matched; returning the top {len(recommendations)}.")

    save_history(twin_id, recommendations)

    return {"recommendations": recommendations, "message": "OK"}


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


def get_recommendation_with_content(raw_learner, exclude_seen_resources=False, limit=MAX_RECOMMENDATIONS):
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
    )

    if not result["recommendations"]:
        result["top_resource_content"] = None
        return result

    top_recommendation = result["recommendations"][0]
    learner = normalize_learner_state(raw_learner)

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

    print("=== FIRST REQUEST ===")
    first = get_recommendations(learner)
    print(f"Returned {len(first['recommendations'])} resource(s).")
    for record in first["recommendations"]:
        print_recommendation(record, detailed=False)

    print("\n\n=== SECOND REQUEST, same question (should be IDENTICAL) ===")
    second = get_recommendations(learner)
    first_urls = [r["url"] for r in first["recommendations"]]
    second_urls = [r["url"] for r in second["recommendations"]]
    print(f"Identical: {first_urls == second_urls}  <- should be True (reproducible)")

    print("\n\n=== THIRD REQUEST: 'recommend something else' ===")
    third = get_recommendations(learner, exclude_seen_resources=True)
    print(f"Message: {third['message']}")
    print(f"Returned {len(third['recommendations'])} resource(s).")
    for record in third["recommendations"]:
        print_recommendation(record, detailed=False)

    third_urls = [r["url"] for r in third["recommendations"]]
    overlap = set(first_urls) & set(third_urls)
    print(f"\nOverlap with first request: {len(overlap)}  <- should be 0 (genuinely new)")