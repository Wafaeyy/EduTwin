"""
Team Beta - Recommendation Engine
Orchestrator Integration Interface.

The single entry point the Orchestrator calls. Its job is validation and
translation only -- it never makes recommendation decisions itself.

LEARNER STATE INPUT
    The engine needs a flat dictionary of exact values it can compare with ==:
        {"twin_id": "...", "level": "beginner", "goal": "machine learning",
         "preferred_format": "video", "preferred_duration": "short"}

    If the Orchestrator sends only its prose context briefing (the string from
    ContextBuilder, written for LLM agents), a Gemini call extracts those
    fields from it -- see twin/context_extractor.py. Structured learner_state
    always wins when both are supplied: it is exact and reproducible, the
    extraction is not, and it costs no API call.

Three intents are supported:

  resource_recommendation
      {"intent": "resource_recommendation",
       "learner_state": {"twin_id": "...", "level": "...", "goal": "...", ...},
       "context": "<prose briefing, used only if learner_state is absent>",
       "user_request": "recommend something else",
       "exclude_seen": true}

      exclude_seen is set by the ORCHESTRATOR, not inferred here. The
      Orchestrator is an LLM and understands what the learner meant, however
      they phrased it. This engine performs no language understanding on the
      user's request -- it acts on the flag deterministically.

      Deep content analysis of the TOP-RANKED resource is included by
      default, returned in the `content` field. The other recommendations are
      NOT analyzed -- one Gemini call per request, not five. Results are
      cached and shared across all learners, so a resource already analyzed
      by anyone costs nothing.

      Pass "include_content": false to skip analysis entirely.

  reject_resources
      {"intent": "reject_resources",
       "learner_state": {"twin_id": "..."},
       "resource_urls": ["https://...", "https://..."]}

      Permanently excludes those resources for that learner.

  analyze_resource_content
      {"intent": "analyze_resource_content",
       "resource_url": "https://...",
       "format": "video",
       "topic": "machine learning"}

      NOT CURRENTLY USED BY THE UI. Built for a planned "What's inside?"
      button on every recommendation, letting the learner pick which resource
      to look into rather than only ever seeing the top one. The current UI
      shows analysis for the top result automatically instead.

      Kept working and tested so the button can be added with no engine
      changes: the UI sends the url and format of whichever card was clicked,
      and this returns that resource's analysis. Works on ANY url, including
      one the learner pasted in that is not in the catalog.
"""

from main import (
    get_recommendations,
    get_recommendation_with_content,
    reject_recommendations,
    analyze_single_resource,
)
from twin.mock_twin import normalize_learner_state
from twin.context_extractor import extract_learner_state

INTENT_RECOMMEND = "resource_recommendation"
INTENT_REJECT = "reject_resources"
INTENT_ANALYZE = "analyze_resource_content"
SUPPORTED_INTENTS = [INTENT_RECOMMEND, INTENT_REJECT, INTENT_ANALYZE]

# The UI shows analysis for the top recommendation automatically, so content
# is included unless the caller explicitly opts out. Flip this to False if the
# UI ever moves to on-demand analysis (see the button note above).
INCLUDE_CONTENT_BY_DEFAULT = True


def error_response(intent, message):
    """Every failure comes back in the same shape as a success, so the
    Orchestrator never has to branch on response structure."""
    return {
        "status": "error",
        "intent": intent,
        "recommendations": [],
        "content": None,
        "content_for_url": None,
        "message": message,
        "warnings": [],
    }


def resolve_learner_state(request):
    """Returns the learner_state to use, and any warning about how.

    Structured learner_state is preferred. Falling back to extracting it from
    the prose briefing costs an API call and is not fully reproducible, so the
    caller is told when that happened.
    """
    learner_state = request.get("learner_state")
    if learner_state:
        return learner_state, None

    context = request.get("context")
    if context:
        extracted = extract_learner_state(context)
        if extracted:
            return extracted, (
                "learner_state was extracted from the context briefing by an LLM. "
                "Send structured learner_state instead for faster, reproducible results."
            )
        return None, "Could not extract learner state from the context briefing; personalization is unavailable."

    return None, None


def handle_recommendation_request(request):
    """Handles the resource_recommendation intent."""
    learner_state, state_warning = resolve_learner_state(request)
    exclude_seen = bool(request.get("exclude_seen", False))
    include_content = bool(request.get("include_content", INCLUDE_CONTENT_BY_DEFAULT))

    if include_content:
        # Analyses ONLY the top-ranked resource -- one Gemini call, not five.
        # A cache hit costs nothing at all.
        result = get_recommendation_with_content(learner_state, exclude_seen_resources=exclude_seen)
        content = result.get("top_resource_content")
    else:
        result = get_recommendations(learner_state, exclude_seen_resources=exclude_seen)
        content = None

    warnings = []
    if state_warning:
        warnings.append(state_warning)

    # Warn (do not fail) if no learner id was supplied: recommendations still
    # work, but nothing can be remembered between requests.
    normalized = normalize_learner_state(learner_state)
    if not normalized.get("twin_id"):
        warnings.append("No twin_id supplied; this request was not recorded and history was not applied.")

    # Tell the caller WHICH resource the content belongs to. Without this the
    # UI has to assume it is the first item, which silently breaks the day
    # anything changes about ordering.
    content_url = result["recommendations"][0]["url"] if result["recommendations"] and include_content else None

    return {
        "status": "ok",
        "intent": INTENT_RECOMMEND,
        "recommendations": result["recommendations"],
        "content": content,
        "content_for_url": content_url,
        "message": result["message"],
        "warnings": warnings,
    }


def handle_rejection_request(request):
    """Handles the reject_resources intent."""
    learner_state, _ = resolve_learner_state(request)
    resource_urls = request.get("resource_urls")

    if not resource_urls:
        return error_response(INTENT_REJECT, "No resource_urls were provided to reject.")

    if not isinstance(resource_urls, list):
        return error_response(INTENT_REJECT, "resource_urls must be a list of urls.")

    normalized = normalize_learner_state(learner_state)
    if not normalized.get("twin_id"):
        return error_response(INTENT_REJECT, "A twin_id is required to record rejections.")

    recorded = reject_recommendations(learner_state, resource_urls)

    return {
        "status": "ok",
        "intent": INTENT_REJECT,
        "recommendations": [],
        "content": None,
        "content_for_url": None,
        "message": f"Recorded {recorded} rejection(s). These resources will not be recommended to this learner again.",
        "warnings": [],
    }


def handle_analysis_request(request):
    """Handles the analyze_resource_content intent.

    NOT CURRENTLY USED BY THE UI -- see the module docstring. Kept working so
    a per-resource "What's inside?" button can be added later with no engine
    changes.
    """
    resource_url = request.get("resource_url")
    if not resource_url:
        return error_response(INTENT_ANALYZE, "A resource_url is required.")

    resource_format = request.get("format")
    topic = request.get("topic")

    # Fall back to the learner's goal if no explicit topic was given -- article
    # analysis flags each section as relevant to this topic or not.
    if not topic:
        learner_state, _ = resolve_learner_state(request)
        normalized = normalize_learner_state(learner_state)
        topic = normalized.get("goal")

    content = analyze_single_resource(resource_url, resource_format, topic)

    return {
        "status": "ok",
        "intent": INTENT_ANALYZE,
        "recommendations": [],
        "content": content,
        "content_for_url": resource_url,
        "message": content.get("access_status", "OK"),
        "warnings": [],
    }


def handle_orchestrator_request(request):
    """Validates the request and routes it to the right handler."""
    if request is None:
        return error_response(None, "No request was provided.")

    if not isinstance(request, dict):
        return error_response(None, "Request must be a dictionary.")

    intent = request.get("intent")

    if intent not in SUPPORTED_INTENTS:
        return error_response(
            intent,
            f"Unsupported intent: {intent!r}. This engine only handles: {SUPPORTED_INTENTS}",
        )

    try:
        if intent == INTENT_RECOMMEND:
            return handle_recommendation_request(request)
        if intent == INTENT_REJECT:
            return handle_rejection_request(request)
        return handle_analysis_request(request)
    except Exception as error:
        # The Orchestrator must never receive a raw traceback -- it gets a
        # structured error it can handle like any other failure.
        print(f"[orchestrator interface] Unhandled error: {error}")
        return error_response(intent, f"The recommendation engine failed: {error}")


if __name__ == "__main__":
    TEST_TWIN = "orchestrator-test-0004"

    learner_state = {
        "twin_id": TEST_TWIN,
        "level": "beginner",
        "goal": "machine learning",
        "preferred_format": "video",
        "preferred_duration": "short",
    }

    SAMPLE_BRIEFING = f"""======================================================================
STUDENT PROFILE & TWIN
======================================================================

Student identifier: {TEST_TWIN}
The learner is at a beginner level and is currently working toward
understanding machine learning. They prefer short videos over long
written material.

======================================================================
RELEVANT MEMORIES
======================================================================

The learner watched an introductory neural networks video last week.
"""

    print("=== 1. Structured learner_state (preferred path, no LLM call) ===")
    result = handle_orchestrator_request({
        "intent": INTENT_RECOMMEND,
        "learner_state": learner_state,
        "user_request": "recommend some machine learning videos",
    })
    print(f"Status: {result['status']} | Warnings: {result['warnings']}")
    for index, record in enumerate(result["recommendations"][:5]):
        marker = "  <- content is for THIS one" if record["url"] == result["content_for_url"] else ""
        print(f"  {index + 1}. {record['score']:>3} | {record['url']}{marker}")

    content = result["content"]
    if content and content.get("chapters"):
        print(f"\n  {len(content['chapters'])} chapters:")
        for chapter in content["chapters"][:4]:
            print(f"    [{chapter['start_time']}] {chapter['topic']}")

    print("\n=== 2. Context briefing only (LLM extraction path) ===")
    from_context = handle_orchestrator_request({
        "intent": INTENT_RECOMMEND,
        "context": SAMPLE_BRIEFING,
        "include_content": False,
    })
    print(f"Status: {from_context['status']}")
    print(f"Warnings: {from_context['warnings']}")
    for record in from_context["recommendations"][:3]:
        print(f"  {record['score']:>3} | {record['url']}")

    print("\n=== 3. Both supplied -- structured must win, no extraction ===")
    both = handle_orchestrator_request({
        "intent": INTENT_RECOMMEND,
        "learner_state": learner_state,
        "context": SAMPLE_BRIEFING,
        "include_content": False,
    })
    extracted_warning = any("extracted from the context" in w for w in both["warnings"])
    print(f"Extraction happened: {extracted_warning}  <- should be False")

    print("\n=== 4. Rejecting the top resource ===")
    if result["recommendations"]:
        rejected = handle_orchestrator_request({
            "intent": INTENT_REJECT,
            "learner_state": {"twin_id": TEST_TWIN},
            "resource_urls": [result["recommendations"][0]["url"]],
        })
        print(rejected["message"])

    print("\n=== 5. Asking again -- rejected one gone, new top analyzed ===")
    after = handle_orchestrator_request({
        "intent": INTENT_RECOMMEND,
        "learner_state": learner_state,
    })
    old_top = result["recommendations"][0]["url"] if result["recommendations"] else None
    new_urls = [r["url"] for r in after["recommendations"]]
    print(f"Rejected resource still present: {old_top in new_urls}  <- should be False")
    print(f"Content now for: {after['content_for_url']}")

    print("\n=== 6. Neither learner_state nor context ===")
    empty = handle_orchestrator_request({
        "intent": INTENT_RECOMMEND,
        "include_content": False,
    })
    print(f"Status: {empty['status']} | Warnings: {empty['warnings']}")

    print("\n=== 7. Unsupported intent ===")
    print(handle_orchestrator_request({"intent": "study_schedule_planning"})["message"])