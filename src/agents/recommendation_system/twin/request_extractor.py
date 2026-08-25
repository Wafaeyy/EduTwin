"""
Extracts what the learner is asking for RIGHT NOW from their message.

Separate from context_extractor.py, which reads the stored Digital Twin
briefing. That gives long-term state ("this learner wants to become an AI
engineer"). This gives the immediate request ("show me videos about calculus").

They are different things and must not be confused: a learner whose goal is
"artificial intelligence" can still ask about calculus today, and the engine
must search for calculus.

Guardrails, all enforced by deterministic code around the call:
  - The prompt lists the ONLY permitted format/level/duration values.
  - The model must return null for anything the message does not state.
  - Any failure returns {} and the caller falls back to the Twin's stored
    preferences, so a failed extraction degrades rather than breaks.
"""

import os
import json

from google import genai

from src.agents.recommendation_system.config import KNOWN_LEVELS, KNOWN_FORMATS, KNOWN_DURATIONS

GEMINI_MODEL = "gemini-3.6-flash"
MAX_REQUEST_CHARACTERS = 2000

REQUEST_FIELDS = ["topic", "format", "level", "duration"]


def build_request_prompt(user_request):
    """Builds a prompt that permits ONLY the engine's known values."""
    truncated = user_request[:MAX_REQUEST_CHARACTERS]

    return f"""You are reading a student's message to a learning assistant and extracting what they are asking for.

Extract ONLY what the message explicitly asks for. Do not infer, guess, or invent anything.

Return a JSON object with exactly these four keys:

"topic": the specific subject the student is asking about, as a short lowercase phrase (for example "calculus", "linear algebra", "machine learning"). This is what they want RIGHT NOW, not their long-term goal. If the message does not name a subject, null.

"format": EXACTLY one of {KNOWN_FORMATS}, or null. Only if the message asks for that kind of resource (for example "videos" -> "video", "a course" -> "course", "something to read" -> "article"). If they did not say, null.

"level": EXACTLY one of {KNOWN_LEVELS}, or null. Only if the message states a difficulty (for example "beginner calculus", "advanced material"). If they did not say, null.

"duration": EXACTLY one of {KNOWN_DURATIONS}, or null. Only if the message states a length (for example "something short", "a quick video"). If they did not say, null.

Rules:
- If the message does not clearly state a value, return null for it. Null is always better than a guess -- the engine falls back to the student's stored preferences when a field is null.
- For format, level and duration you must copy a value from the lists above character for character, or return null.
- Respond with ONLY the JSON object. No explanation, no markdown code fences.

Examples:
Message: "recommend videos about calculus"
{{"topic": "calculus", "format": "video", "level": null, "duration": null}}

Message: "recommend something for me"
{{"topic": null, "format": null, "level": null, "duration": null}}

Message: "I need a short beginner course on linear algebra"
{{"topic": "linear algebra", "format": "course", "level": "beginner", "duration": "short"}}

Student message:
{truncated}
"""


def parse_json_response(response_text):
    """Strips code fences and parses. Returns None if unparseable."""
    cleaned = response_text.strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as error:
        print(f"[request extractor] Could not parse the model's response as JSON ({error}).")
        return None

    if not isinstance(parsed, dict):
        print("[request extractor] Model returned something that is not a JSON object.")
        return None

    return parsed


def extract_request(user_request):
    """Turns the learner's message into {topic, format, level, duration}.

    Any value the message does not state comes back as None, and the caller
    then falls back to the learner's stored preference for that field.

    Returns {} on any failure -- the engine proceeds on stored state alone.
    """
    if not user_request or not user_request.strip():
        return {}

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key is None:
        print("[request extractor] GEMINI_API_KEY is not set; cannot read the request.")
        return {}

    prompt = build_request_prompt(user_request)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    except Exception as error:
        print(f"[request extractor] Gemini call failed ({error}); using stored preferences only.")
        return {}

    extracted = parse_json_response(response.text)
    if extracted is None:
        return {}

    # Keep only the four fields we asked for. Anything else the model decided
    # to add is discarded before it can reach the engine.
    request_state = {key: extracted.get(key) for key in REQUEST_FIELDS}

    # Reject any value outside the known lists -- the model cannot introduce a
    # value the engine would not otherwise accept.
    if request_state["level"] not in KNOWN_LEVELS:
        request_state["level"] = None
    if request_state["format"] not in KNOWN_FORMATS:
        request_state["format"] = None
    if request_state["duration"] not in KNOWN_DURATIONS:
        request_state["duration"] = None

    print(f"[request extractor] Learner is asking for: {request_state}")
    return request_state


if __name__ == "__main__":
    for message in [
        "recommend videos about calculus",
        "recommend something for me",
        "I need a short beginner course on linear algebra",
        "show me research papers on transformers",
        "",
    ]:
        print(f"\n{message!r}")
        print(f"  -> {extract_request(message)}")