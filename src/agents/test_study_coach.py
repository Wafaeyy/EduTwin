"""
Multi-turn test harness for the Study Coach agent.

Replays a scripted conversation against the Coach, carrying history forward so
the model can see earlier turns. The model itself is stateless — every call is
independent — so anything it should "remember" must be serialized into the
prompt by this script.

Run from the project root:
    python src/agents/test_study_coach.py
"""

from google import genai
from google.genai import types
from src.retrieval.retrieval_orchestrator import RetrievalOrchestrator
from src.retrieval.context_builder import ContextBuilder
##import all b2a ya basha
## ContextBuilder.build(RetrievalOrchestrator.retrieve(twin,query)) instead of build_briefing
client = genai.Client()  # reads GEMINI_API_KEY from the environment

MODEL = "gemini-3.6-flash"

# ── static recipe: the versioned prompt artifact ──────────────────────────────
system_prompt = open(
    "src/agents/prompts/coach_system_v2.txt", encoding="utf-8"
).read()

# ── mock Twin: stand-in until the real Twin is live ───────────────────────────
# NOTE: known_misconceptions still flags the chain rule, while the scripted
# turns below show the student applying it correctly. This is deliberate — it
# tests the CONTRADICTION CHECK and the briefing_contradicted signal.
twin = {
    "learning_style": "example-driven",
    "concept_mastery": {"limits": 0.85, "derivatives": 0.35, "chain_rule": 0.20},
    "recent_errors": [
        "differentiated sin(2x) as cos(2x), dropping the inner derivative"
    ],
    "known_misconceptions": [
        "thinks the chain rule is optional when the inside looks simple"
    ],
}


def build_briefing(t):
    """Render the Twin slice as the text that goes in the <briefing> slot.

    This rendering is the A/B/C experimental variable — vary this function,
    hold retrieval constant.
    """
    return "\n".join(
        [
            f"Learning style: {t['learning_style']}",
            "Concept mastery (0-1): "
            + ", ".join(f"{k}={v}" for k, v in t["concept_mastery"].items()),
            "Recent errors: " + "; ".join(t["recent_errors"]),
            "Known misconceptions: " + "; ".join(t["known_misconceptions"]),
        ]
    )


intent = "concept_explanation"  # STUB: hardcoded until the intent classifier exists

# ── the scripted conversation ─────────────────────────────────────────────────
# Three DISTINCT problems, all answered correctly. By turn 3 the 0.8-0.9
# confidence anchor ("two or more distinct problems within this session")
# becomes reachable — but only because history is passed forward.
student_turns = [
    "For sin(2x) I take cos(2x) and multiply by the derivative of the inside, "
    "which is 2, so 2cos(2x) — right?",
    "And sin(5x) would be 5cos(5x).",
    "So cos(3x) is -3sin(3x)?",
]

history = []  # application-side memory; substitutes for the model having none

for turn_index, student_question in enumerate(student_turns, start=1):

    # Emit the history block only when there is history, so turn 1 never sends
    # an empty tag (an empty tag invites the model to invent content for it).
    history_block = ""
    if history:
        history_block = (
            "<conversation_so_far>\n"
            + "\n".join(history)
            + "\n</conversation_so_far>\n\n"
        )

    user_block = f"""{history_block}<student_message>
{student_question}
</student_message>

<intent>
{intent}
</intent>

<briefing>
{build_briefing(twin)}
</briefing>"""

    resp = client.models.generate_content(
        model=MODEL,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
        contents=user_block,
    )
    reply = resp.text

    print(f"\n{'=' * 70}")
    print(f"TURN {turn_index}")
    print(f"{'=' * 70}")
    print(f"STUDENT: {student_question}\n")
    print(f"COACH:\n{reply}")

    # Record both sides AFTER the call — `reply` does not exist before it.
    # The Coach's own turns matter too, or turn 3 reads as three disconnected
    # student utterances rather than a dialogue.
    history.append(f"Student: {student_question}")
    history.append(f"Coach: {reply}")