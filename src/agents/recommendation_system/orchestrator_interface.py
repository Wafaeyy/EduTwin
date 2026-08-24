"""
Team Beta - Recommendation Engine
Orchestrator Integration Interface.

SIMPLEST ENTRY POINTS -- pick one:

    from orchestrator_interface import recommend_text, recommend_from_briefing

    text = recommend_text(briefing_string)          # STRING in, STRING out
    data = recommend_from_briefing(briefing_string) # STRING in, DICT out

Both take the ContextBuilder's prose briefing as a plain string. An internal
LLM call extracts the learner's twin_id, goal, level, preferred format and
preferred duration from it; everything after that point is deterministic code:
retrieval, verification, scoring, ranking, learner history, and deep content
analysis of the top result.

Use recommend_text() when you just want something to show the learner.
Use recommend_from_briefing() when the interface needs the individual fields --
clickable links, score badges, a reject button. Those values cannot be
recovered reliably from formatted text.

handle_orchestrator_request() below is the full dict-based interface. It is
what both of the above call internally, and it additionally supports recording
learner rejections and analysing one specific chosen resource.

LEARNER STATE INPUT
    The engine needs a flat dictionary of exact values it can compare with ==:
        {"twin_id": "...", "level": "beginner", "goal": "machine learning",
         "preferred_format": "video", "preferred_duration": "short"}

    If only the prose briefing is available, a Gemini call extracts those
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

      Permanently excludes those resources for that learner. Different from
      exclude_seen, which is temporary ("show me different ones this time").
      A rejection is forever, and survives across sessions.

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

from src.agents.recommendation_system.main import (
    get_recommendations,
    get_recommendation_with_content,
    reject_recommendations,
    analyze_single_resource,
)
from src.agents.recommendation_system.twin.mock_twin import normalize_learner_state
from src.agents.recommendation_system.twin.context_extractor import extract_learner_state

INTENT_RECOMMEND = "resource_recommendation"
INTENT_REJECT = "reject_resources"
INTENT_ANALYZE = "analyze_resource_content"
SUPPORTED_INTENTS = [INTENT_RECOMMEND, INTENT_REJECT, INTENT_ANALYZE]

# The UI shows analysis for the top recommendation automatically, so content
# is included unless the caller explicitly opts out. Flip this to False if the
# UI ever moves to on-demand analysis (see the button note above).
INCLUDE_CONTENT_BY_DEFAULT = True


# ---------------------------------------------------------------------------
# Simple entry points
# ---------------------------------------------------------------------------

def recommend_from_briefing(briefing, something_else=False, include_content=True):
    """Takes the Orchestrator's prose briefing STRING, returns a structured dict.

        response = recommend_from_briefing(briefing_string)

        response["recommendations"]   -> list of resources to display
        response["content"]           -> chapters/sections for the top one
        response["content_for_url"]   -> which resource that content belongs to
        response["message"]           -> show this when recommendations is empty

    something_else=True means the learner asked for DIFFERENT resources than
    they were given before: everything already shown to them is excluded, and
    discovery searches with varied phrasings for genuinely new material.

    include_content=False skips deep analysis of the top result, which makes
    the response noticeably faster.

    Never raises. A bad or empty briefing comes back as a structured error.
    """
    if not isinstance(briefing, str):
        return error_response(
            INTENT_RECOMMEND,
            f"recommend_from_briefing expects a string, got {type(briefing).__name__}.",
        )

    if not briefing.strip():
        return error_response(INTENT_RECOMMEND, "The briefing was empty.")

    return handle_orchestrator_request({
        "intent": INTENT_RECOMMEND,
        "context": briefing,
        "exclude_seen": bool(something_else),
        "include_content": bool(include_content),
    })


def format_response_as_text(response):
    """Turns the engine's structured response into readable display text.

    Everything here comes from the response itself -- nothing is invented. The
    reasons are already human-readable and generated directly from the score
    breakdown, so they can be shown to a learner verbatim.
    """
    if response["status"] != "ok":
        return f"Sorry, something went wrong: {response['message']}"

    recommendations = response["recommendations"]
    if not recommendations:
        return response["message"]

    lines = []
    count = len(recommendations)
    lines.append(f"Found {count} resource{'s' if count != 1 else ''} for you:")
    lines.append("")

    content = response.get("content")
    content_url = response.get("content_for_url")

    for index, record in enumerate(recommendations, start=1):
        lines.append(f"{index}. {record['resource']}")
        lines.append(f"   Link:  {record['url']}")

        resource_type = record["format"] or "unknown type"
        lines.append(f"   Type:  {resource_type}   |   Match: {record['score']}/100")

        if record["reasons"]:
            lines.append("   Why this one:")
            for reason in record["reasons"]:
                lines.append(f"     - {reason}")

        # Deep analysis belongs to exactly ONE resource. Match by url, never by
        # position -- if ranking changes, position attaches it to the wrong
        # resource silently.
        if content and record["url"] == content_url:
            if content.get("access_status") == "ok":
                chapters = content.get("chapters")
                sections = content.get("sections")

                if chapters:
                    lines.append("")
                    lines.append(f"   What's inside ({len(chapters)} chapters):")
                    for chapter in chapters:
                        lines.append(f"     [{chapter['start_time']}] {chapter['topic']}")
                        if chapter.get("summary"):
                            lines.append(f"          {chapter['summary']}")

                elif sections:
                    lines.append("")
                    lines.append(f"   What's inside ({len(sections)} sections):")
                    for section in sections:
                        mark = "*" if section.get("relevant_to_requested_topic") else " "
                        lines.append(f"    {mark} {section['heading']}")
                        if section.get("summary"):
                            lines.append(f"          {section['summary']}")
                    lines.append("     (* = directly relevant to your goal)")
            else:
                lines.append(f"   Could not look inside this one: {content.get('access_status')}")

        lines.append("")

    return "\n".join(lines).rstrip()


def recommend_text(briefing, something_else=False, include_content=True):
    """Same as recommend_from_briefing(), but returns READY-TO-DISPLAY TEXT.

        text = recommend_text(briefing_string)
        print(text)          # or put it straight into a GUI text area

    Use this when you just want something to show the learner. If you need to
    build interactive cards -- clickable links, score badges, a reject button
    -- use recommend_from_briefing() instead and read the fields directly;
    those values cannot be recovered reliably from formatted text.
    """
    response = recommend_from_briefing(
        briefing,
        something_else=something_else,
        include_content=include_content,
    )
    return format_response_as_text(response)


# ---------------------------------------------------------------------------
# Full dict-based interface
# ---------------------------------------------------------------------------

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
                "Extraction is not fully reproducible; the same briefing may "
                "occasionally yield a different level or format."
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
    TEST_TWIN = "briefing-test-0001"

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

    print("=" * 70)
    print("TEST 1 -- recommend_text(): STRING in, STRING out")
    print("=" * 70)
    print()
    print(recommend_text(SAMPLE_BRIEFING))

    print()
    print("=" * 70)
    print("TEST 2 -- recommend_from_briefing(): STRING in, DICT out")
    print("=" * 70)
    response = recommend_from_briefing(SAMPLE_BRIEFING, include_content=False)
    print(f"Status: {response['status']} | {response['message']}")
    for index, record in enumerate(response["recommendations"][:5], start=1):
        print(f"  {index}. {record['score']:>3} | {record['url']}")
    print(f"  Warnings: {response['warnings']}")

    print()
    print("=" * 70)
    print("TEST 3 -- same briefing twice should be IDENTICAL")
    print("=" * 70)
    again = recommend_from_briefing(SAMPLE_BRIEFING, include_content=False)
    first_urls = [r["url"] for r in response["recommendations"]]
    again_urls = [r["url"] for r in again["recommendations"]]
    print(f"Identical: {first_urls == again_urls}  <- should be True")

    print()
    print("=" * 70)
    print("TEST 4 -- 'recommend something else'")
    print("=" * 70)
    different = recommend_text(SAMPLE_BRIEFING, something_else=True, include_content=False)
    print(different)

    print()
    print("=" * 70)
    print("TEST 5 -- bad input handled cleanly")
    print("=" * 70)
    print(f"Empty string:  {recommend_text('')}")
    print(f"Wrong type:    {recommend_text({'not': 'a string'})}")