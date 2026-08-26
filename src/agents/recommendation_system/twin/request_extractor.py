"""
Extracts what the learner is asking for RIGHT NOW from their message.

Separate from context_extractor.py, which reads the stored Digital Twin
briefing. That gives long-term state ("this learner wants to become an AI
engineer"). This gives the immediate request ("show me 10 videos about
calculus").

THREE LAYERS, cheapest and most reliable first:
  1. Cache        -- this exact message was read before; no API call.
  2. Gemini       -- full understanding, handles any phrasing and any language.
  3. Keywords     -- deterministic pattern matching when Gemini is unavailable.

Layer 3 exists because Gemini failed repeatedly during development (429 quota,
503 overload). With no extraction at all, every recommendation scored 0/100.

The extracted topic is used DIRECTLY as an internet search query, so
abbreviations are expanded: "calc" must become "calculus", not stay as
shorthand, which searches badly.

Guardrails, all enforced by deterministic code around the Gemini call:
  - The prompt lists the ONLY permitted format/level/duration values.
  - The model must return null for anything the message does not state.
  - Every returned value is checked before use -- including the count, which
    is clamped to a sane range so "give me 500 videos" cannot run away.
  - Any failure falls through to the next layer rather than breaking.
"""

import os
import re
import json

from google import genai

from src.agents.recommendation_system.config import KNOWN_LEVELS, KNOWN_FORMATS, KNOWN_DURATIONS
from src.agents.recommendation_system.database.persistence import save_extraction, load_extraction

GEMINI_MODEL = "gemini-3.5-flash"
MAX_REQUEST_CHARACTERS = 2000

REQUEST_FIELDS = ["topic", "format", "level", "duration", "count"]

# A learner may ask for a specific number of recommendations. Clamped so a
# careless or malicious "give me 500 videos" cannot trigger hundreds of
# network verifications.
MIN_REQUESTED_COUNT = 1
MAX_REQUESTED_COUNT = 20

# Used by the keyword fallback only. Gemini handles these itself.
ABBREVIATIONS = {
    "calc": "calculus",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "linalg": "linear algebra",
    "ds": "data structures",
    "os": "operating systems",
    "db": "databases",
    "stats": "statistics",
    "algo": "algorithms",
    "oop": "object oriented programming",
}

FORMAT_WORDS = {
    "video": "video", "videos": "video", "watch": "video",
    "course": "course", "courses": "course",
    "article": "article", "articles": "article", "read": "article", "blog": "article",
    "book": "book", "books": "book",
    "tutorial": "tutorial", "tutorials": "tutorial",
    "documentation": "documentation", "docs": "documentation",
    "paper": "research_paper", "papers": "research_paper", "research": "research_paper",
    "practice": "practice_platform", "exercises": "practice_platform",
    "playlist": "playlist", "playlists": "playlist",
}

LEVEL_WORDS = {
    "beginner": "beginner", "beginners": "beginner", "basic": "beginner",
    "basics": "beginner", "introductory": "beginner", "intro": "beginner",
    "intermediate": "intermediate",
    "advanced": "advanced", "expert": "advanced",
}

DURATION_WORDS = {
    "short": "short", "quick": "short", "brief": "short",
    "medium": "medium",
    "long": "long", "full": "long", "complete": "long", "comprehensive": "long",
}

# Spelled-out numbers, for the keyword fallback.
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
    "a": 1, "an": 1, "couple": 2, "few": 3, "several": 3,
}

TOPIC_MARKERS = ["about", "on", "for", "regarding", "concerning", "related to"]

NOISE_WORDS = set(FORMAT_WORDS) | set(LEVEL_WORDS) | set(DURATION_WORDS) | set(NUMBER_WORDS) | {
    "recommend", "recommendation", "recommendations", "suggest", "give", "show",
    "find", "want", "need", "me", "some", "any", "please", "how", "to", "learn",
    "learning", "study", "a", "an", "the", "i", "my", "of", "in", "and", "or",
    "something", "stuff", "things", "resource", "resources", "material",
    "materials", "play", "get", "can", "you",
}


def clamp_count(value):
    """Turns whatever came back into a usable count, or None.

    Anything unparseable, zero, negative, or absurdly large becomes None or is
    pulled into range -- the caller then uses the default.
    """
    if value is None:
        return None
    try:
        count = int(value)
    except (TypeError, ValueError):
        return None
    if count < MIN_REQUESTED_COUNT:
        return None
    return min(count, MAX_REQUESTED_COUNT)


def expand_abbreviation(topic):
    """Turns 'calc' into 'calculus'. Only used by the keyword fallback."""
    if not topic:
        return topic
    lowered = topic.strip().lower()
    return ABBREVIATIONS.get(lowered, lowered)


def extract_by_keywords(user_request):
    """Deterministic fallback: reads what it can with pattern matching.

    Deliberately conservative. It returns None for anything it cannot find
    with confidence, and the engine then falls back to the learner's stored
    preference for that field.
    """
    text = user_request.lower()
    words = re.findall(r"[a-z0-9+#]+", text)

    found = {"topic": None, "format": None, "level": None, "duration": None, "count": None}

    # A digit anywhere is the most likely count: "10 videos", "give me 3".
    digits = re.findall(r"\b(\d{1,3})\b", text)
    if digits:
        found["count"] = clamp_count(digits[0])

    for word in words:
        if found["format"] is None and word in FORMAT_WORDS:
            found["format"] = FORMAT_WORDS[word]
        if found["level"] is None and word in LEVEL_WORDS:
            found["level"] = LEVEL_WORDS[word]
        if found["duration"] is None and word in DURATION_WORDS:
            found["duration"] = DURATION_WORDS[word]
        # Only trust a spelled-out number if no digit was found, and skip
        # "a"/"an" here -- they are far too common to mean "one resource".
        if found["count"] is None and word in NUMBER_WORDS and word not in ("a", "an"):
            found["count"] = clamp_count(NUMBER_WORDS[word])

    # Topic: prefer whatever follows a marker word ("about", "on", "for"),
    # since that is where people put the subject.
    topic_words = []
    for marker in TOPIC_MARKERS:
        match = re.search(rf"\b{marker}\b(.+)", text)
        if match:
            topic_words = [w for w in re.findall(r"[a-z0-9+#]+", match.group(1))
                           if w not in NOISE_WORDS and not w.isdigit()]
            if topic_words:
                break

    if not topic_words:
        topic_words = [w for w in words if w not in NOISE_WORDS and not w.isdigit()]

    if topic_words:
        raw_topic = " ".join(topic_words)
        found["topic"] = expand_abbreviation(raw_topic) if len(topic_words) == 1 else raw_topic

    return found


def build_request_prompt(user_request):
    """Builds a prompt that permits ONLY the engine's known values."""
    truncated = user_request[:MAX_REQUEST_CHARACTERS]

    return f"""You are reading a student's message to a learning assistant and extracting what they are asking for.

Extract ONLY what the message explicitly asks for. Do not infer, guess, or invent anything.

Return a JSON object with exactly these five keys:

"topic": the specific subject the student is asking about, as a short lowercase phrase. This is what they want RIGHT NOW, not their long-term goal. If the message does not name a subject, null.

IMPORTANT: expand abbreviations and shorthand into the full, standard subject name, because this value is used directly as an internet search query. Examples: "calc" -> "calculus", "ml" -> "machine learning", "ai" -> "artificial intelligence", "linalg" -> "linear algebra", "ds" -> "data structures", "dl" -> "deep learning", "nlp" -> "natural language processing", "stats" -> "statistics", "algo" -> "algorithms". Use the full name a textbook would use. Leave proper nouns (names of people, games, products) exactly as written.

"format": EXACTLY one of {KNOWN_FORMATS}, or null. Only if the message asks for that kind of resource (for example "videos" -> "video", "a course" -> "course", "something to read" -> "article"). If they did not say, null.

"level": EXACTLY one of {KNOWN_LEVELS}, or null. Only if the message states a difficulty. If they did not say, null.

"duration": EXACTLY one of {KNOWN_DURATIONS}, or null. Only if the message states a length. If they did not say, null.

"count": how many resources the student asked for, as a whole number, or null. Only if the message gives a number, in digits or words ("10 videos" -> 10, "three courses" -> 3, "a couple of articles" -> 2). Vague words like "some" or "a few resources" that give no clear number are null. If they did not ask for a specific amount, null.

Rules:
- If the message does not clearly state a value, return null for it. Null is always better than a guess -- the engine falls back to the student's stored preferences and defaults when a field is null.
- For format, level and duration you must copy a value from the lists above character for character, or return null.
- Respond with ONLY the JSON object. No explanation, no markdown code fences.

Examples:
Message: "recommend videos about calc"
{{"topic": "calculus", "format": "video", "level": null, "duration": null, "count": null}}

Message: "give me 10 videos about machine learning"
{{"topic": "machine learning", "format": "video", "level": null, "duration": null, "count": 10}}

Message: "I want to learn ML"
{{"topic": "machine learning", "format": null, "level": null, "duration": null, "count": null}}

Message: "show me three beginner python courses"
{{"topic": "python", "format": "course", "level": "beginner", "duration": null, "count": 3}}

Message: "recommend something for me"
{{"topic": null, "format": null, "level": null, "duration": null, "count": null}}

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


def clean_request_state(raw):
    """Keeps only the five expected fields and rejects unknown values."""
    state = {key: raw.get(key) for key in REQUEST_FIELDS}

    if state["level"] not in KNOWN_LEVELS:
        state["level"] = None
    if state["format"] not in KNOWN_FORMATS:
        state["format"] = None
    if state["duration"] not in KNOWN_DURATIONS:
        state["duration"] = None
    state["count"] = clamp_count(state["count"])

    return state


def extract_request(user_request, use_cache=True):
    """Turns the learner's message into {topic, format, level, duration, count}.

    Tries the cache, then Gemini, then keyword matching. Any value that cannot
    be determined comes back as None, and the caller falls back to the
    learner's stored preference or the engine default for that field.
    """
    if not user_request or not user_request.strip():
        return {}

    # Layer 1: cache. Free, instant, and immune to Gemini being down.
    if use_cache:
        try:
            cached = load_extraction(user_request)
            if cached is not None:
                print(f"[request extractor] Cache hit: {cached}")
                return cached
        except Exception as error:
            print(f"[request extractor] Could not read cache ({error}); extracting fresh.")

    # Layer 2: Gemini.
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key is not None:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL, contents=build_request_prompt(user_request)
            )
            extracted = parse_json_response(response.text)
            if extracted is not None:
                request_state = clean_request_state(extracted)
                print(f"[request extractor] Learner is asking for: {request_state}")
                try:
                    save_extraction(user_request, "request", request_state)
                except Exception as error:
                    print(f"[request extractor] Could not cache extraction ({error}).")
                return request_state
        except Exception as error:
            print(f"[request extractor] Gemini unavailable ({error}); falling back to keyword matching.")
    else:
        print("[request extractor] GEMINI_API_KEY is not set; falling back to keyword matching.")

    # Layer 3: deterministic keywords. Not as good, but far better than
    # nothing -- with no extraction at all, every recommendation scores 0/100.
    request_state = clean_request_state(extract_by_keywords(user_request))
    print(f"[request extractor] Keyword fallback found: {request_state}")

    # Deliberately NOT cached: a keyword result should never be reused in
    # place of the better Gemini answer once the API recovers.
    return request_state


if __name__ == "__main__":
    MESSAGES = [
        "recommend videos about calc",
        "give me 10 videos about machine learning",
        "show me three beginner python courses",
        "I want a couple of articles on transformers",
        "recomend for me videos about how to play noita",
        "recommend something for me",
        "give me 500 videos about python",
    ]

    print("=" * 60)
    print("KEYWORD FALLBACK ONLY (no Gemini, no cache)")
    print("=" * 60)
    for message in MESSAGES:
        print(f"\n{message!r}")
        print(f"  -> {clean_request_state(extract_by_keywords(message))}")

    print()
    print("=" * 60)
    print("FULL EXTRACTION (cache -> Gemini -> keywords)")
    print("=" * 60)
    for message in MESSAGES:
        print(f"\n{message!r}")
        print(f"  -> {extract_request(message)}")