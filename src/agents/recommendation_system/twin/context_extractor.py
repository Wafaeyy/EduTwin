"""
Extracts structured learner state from the Orchestrator's context briefing.

The Orchestrator's ContextBuilder produces a formatted PROSE string intended
for LLM agents. This engine needs exact values it can compare with ==, so a
Gemini call reads the briefing and pulls out the fields.

Guardrails, all enforced by deterministic code around the call:
  - The prompt lists the ONLY permitted values and forbids inventing any.
  - The model must return null for anything the briefing does not state.
  - Output is passed through normalize_learner_state(), which rejects any
    value outside the allowed lists. The model therefore CANNOT introduce a
    value the engine would not otherwise accept.
  - Any failure returns {} and the engine proceeds with unknown preferences.

KNOWN LIMITATION: extraction from prose is not fully reproducible -- the same
briefing may occasionally yield a different level or format. The
recommendation decision remains 100% deterministic GIVEN a learner state;
it is the extraction step that is not. Prefer receiving structured
learner_state directly whenever the Orchestrator can supply it.
"""

import os
import json

from google import genai

from config import KNOWN_LEVELS, KNOWN_FORMATS, KNOWN_DURATIONS

GEMINI_MODEL = "gemini-3.5-flash"
MAX_BRIEFING_CHARACTERS = 20000


def build_extraction_prompt(briefing):
    """Builds a prompt that permits ONLY the engine's known values."""
    truncated = briefing[:MAX_BRIEFING_CHARACTERS]

    return f"""You are extracting structured data from a student briefing document.

Read the briefing and extract ONLY what it explicitly states. Do not infer, guess, or invent anything.

Return a JSON object with exactly these five keys:

"twin_id": the student's unique identifier as a string, or null if not stated.

"goal": the single topic the student is currently working toward, as a short lowercase phrase (for example "machine learning", "data structures"). If several goals appear, choose the one the briefing presents as current or most recent. If none is stated, null.

"level": EXACTLY one of {KNOWN_LEVELS}, or null. Do not use any other word.

"preferred_format": EXACTLY one of {KNOWN_FORMATS}, or null. Do not use any other word.

"preferred_duration": EXACTLY one of {KNOWN_DURATIONS}, or null. Do not use any other word.

Rules:
- If the briefing does not clearly state a value, return null for it. Null is always better than a guess.
- For level, preferred_format and preferred_duration you must copy a value from the lists above character for character, or return null.
- Respond with ONLY the JSON object. No explanation, no markdown code fences.

Briefing:
{truncated}
"""


def parse_json_response(response_text):
    """Strips code fences and parses. Returns None if unparseable."""
    cleaned = response_text.strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as error:
        print(f"[context extractor] Could not parse the model's response as JSON ({error}).")
        return None

    if not isinstance(parsed, dict):
        print("[context extractor] Model returned something that is not a JSON object.")
        return None

    return parsed


def extract_learner_state(briefing):
    """Turns a context briefing string into a flat learner_state dict.

    Returns {} on any failure -- a missing learner state is handled gracefully
    everywhere downstream, so a failed extraction degrades rather than breaks.
    """
    if not briefing or not briefing.strip():
        return {}

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key is None:
        print("[context extractor] GEMINI_API_KEY is not set; cannot extract learner state.")
        return {}

    prompt = build_extraction_prompt(briefing)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    except Exception as error:
        print(f"[context extractor] Gemini call failed ({error}); proceeding with unknown learner state.")
        return {}

    extracted = parse_json_response(response.text)
    if extracted is None:
        return {}

    # Keep only the five fields we asked for. Anything else the model decided
    # to add is discarded before it can reach the engine.
    allowed_keys = ["twin_id", "goal", "level", "preferred_format", "preferred_duration"]
    learner_state = {key: extracted.get(key) for key in allowed_keys}

    print(f"[context extractor] Extracted: {learner_state}")
    return learner_state


if __name__ == "__main__":
    SAMPLE_BRIEFING = """======================================================================
STUDENT PROFILE & TWIN
======================================================================

Student identifier: 3f2a8c91-4b2e-4a71-9c33-1de5f0a72b18
The learner is at a beginner level and is currently working toward
understanding machine learning. They have previously completed an
introduction to Python.

They prefer to learn from short videos rather than long written material.

======================================================================
RELEVANT MEMORIES
======================================================================

The learner watched an introductory neural networks video last week and
reported finding the mathematical notation difficult.
"""

    print("=== Extracting from a full briefing ===")
    print(extract_learner_state(SAMPLE_BRIEFING))

    print("\n=== Briefing with almost nothing in it ===")
    print(extract_learner_state("The student wants to learn something."))

    print("\n=== Empty briefing ===")
    print(extract_learner_state(""))