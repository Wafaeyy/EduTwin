"""
Live pipeline test: Study Coach -> Explainability.

Nothing is mocked between the two agents. The Coach runs for real, and what it
produces is what the explainer receives. Only the Twin is mocked, same as every
other harness.

One thing IS removed in between: the Coach's <signal> blocks. Signals report
what was observed about the student, for the Twin. The explainer's job is
explaining why the REPLY looks the way it does, so it sees only the
student-facing text.

Two API calls per scenario, so the free-tier sleep applies twice.

Run from the project root:
    python src/agents/test_explain_pipeline.py
"""

import re
import time

from google import genai
from google.genai import types, errors

client = genai.Client()

MODEL = "gemini-3.6-flash"

coach_prompt = open(
    "src/agents/prompts/coach_system_v3.txt", encoding="utf-8"
).read()
explain_prompt = open(
    "src/agents/prompts/explain_v1.txt", encoding="utf-8"
).read()


def strip_signals(text):
    """Drop <signal>...</signal> blocks, keep the student-facing reply.

    .*?      matches as little as possible, so two signal blocks are two
             separate matches rather than one giant one
    DOTALL   lets . match newlines, since a signal spans several lines
    """
    return re.sub(r"<signal>.*?</signal>", "", text, flags=re.DOTALL).strip()


def call(system_prompt, user_block, attempts=3):
    """One API call, retrying on transient 503s from Google's side."""
    for i in range(attempts):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                ),
                contents=user_block,
            )
            return resp.text
        except errors.ServerError:
            if i == attempts - 1:
                raise
            time.sleep(20)


def build_briefing(t):
    """Render the Twin slice. Same shape the Coach harness uses."""
    lines = []
    if t.get("learning_style"):
        lines.append(f"Learning style: {t['learning_style']}")
    if t.get("concept_mastery"):
        lines.append(
            "Concept mastery (0-1): "
            + ", ".join(f"{k}={v}" for k, v in t["concept_mastery"].items())
        )
    if t.get("recent_errors"):
        lines.append("Recent errors: " + "; ".join(t["recent_errors"]))
    if t.get("known_misconceptions"):
        lines.append(
            "Known misconceptions: " + "; ".join(t["known_misconceptions"])
        )
    return "\n".join(lines)


def run_scenario(scenario):
    print(f"\n\n{'#' * 78}")
    print(f"# {scenario['name']}")
    print(f"{'#' * 78}")
    print(f"\nWHAT TO WATCH:\n{scenario['what_to_watch']}\n")

    twin = scenario["twin"]
    briefing = build_briefing(twin)
    student_message = scenario["student_message"]

    # ── Stage 1: the Coach runs for real ────────────────────────────────────
    coach_input = f"""<student_message>
{student_message}
</student_message>

<intent>
{scenario['intent']}
</intent>

<briefing>
{briefing}
</briefing>"""

    coach_output = call(coach_prompt, coach_input)
    student_text = strip_signals(coach_output)

    print(f"{'=' * 70}")
    print("STAGE 1 — COACH (raw, signals included)")
    print(f"{'=' * 70}")
    print(f"STUDENT: {student_message}\n")
    print(f"COACH:\n{coach_output}")

    time.sleep(15)

    # ── Stage 2: the explainer sees the STRIPPED reply ──────────────────────
    # student_text, not coach_output — the explainer gets what the student
    # would see, with the signal blocks removed.
    explain_input = f"""<student_message>
{student_message}
</student_message>

<intent>
{scenario['intent']}
</intent>

<agent_name>
study_coach
</agent_name>

<briefing>
{briefing}
</briefing>

<agent_output>
{student_text}
</agent_output>"""

    explain_output = call(explain_prompt, explain_input)

    print(f"\n{'=' * 70}")
    print("STAGE 2 — EXPLAINABILITY")
    print(f"{'=' * 70}")
    print(explain_output)

    time.sleep(15)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO E1 — well-grounded, example-driven
# ─────────────────────────────────────────────────────────────────────────────
# The briefing supplies three distinct facts that should each show up as a
# separate line of evidence: the weak concept (what to teach), the learning
# style (what form), and the recent error (which example to use).
SCENARIO_E1 = {
    "name": "E1 — Well-grounded explanation",
    "what_to_watch": (
        "1. Does <record> come FIRST, then <rationale>? Order is the whole\n"
        "   point — the rationale must render the record, not invent a story.\n"
        "2. Does 'evidence' pair each briefing fact with the CHOICE it\n"
        "   accounts for, e.g. 'style=example-driven -> opened with a worked\n"
        "   example'? A bare list of briefing facts is not an explanation.\n"
        "3. Confidence should be 0.8-0.9: the concept choice AND the form are\n"
        "   each grounded in a distinct fact.\n"
        "4. 'alternative' should probably be null. The student asked about the\n"
        "   chain rule and got the chain rule — nothing lost. If it invents a\n"
        "   rejected option here, the null rule is not holding.\n"
        "5. Does the rationale avoid mentioning agents, briefings, or scores?\n"
        "6. derivatives_basic=0.85 is in the briefing but caused no visible\n"
        "   choice. It should NOT appear in the evidence list."
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {"chain_rule": 0.20, "derivatives_basic": 0.85},
        "recent_errors": ["differentiated sin(2x) as cos(2x)"],
    },
    "intent": "concept_explanation",
    "student_message": "Can you explain the chain rule?",
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO E2 — thin briefing
# ─────────────────────────────────────────────────────────────────────────────
# One mastery score, nothing else. The Coach will still answer well — it always
# does — but the explainer has very little to work with.
#
# There is no single right answer here. Low confidence is honest. The flag is
# defensible. What would be WRONG is a confident explanation citing evidence
# that is not in the briefing.
SCENARIO_E2 = {
    "name": "E2 — Thin briefing (little to ground on)",
    "what_to_watch": (
        "1. The briefing has ONE fact. The Coach will still produce a good,\n"
        "   detailed reply.\n"
        "2. ACCEPTABLE: low confidence (0.4-0.6), or the flag.\n"
        "3. WRONG: a confident record citing evidence the briefing does not\n"
        "   contain — 'the student prefers examples', 'the student struggles\n"
        "   with algebra'. That is invention, and it is the failure this\n"
        "   agent exists to prevent.\n"
        "4. Watch whether it justifies the choice with SUBJECT knowledge\n"
        "   ('integration by parts is standard for products') instead of\n"
        "   briefing evidence. The prompt forbids this explicitly."
    ),
    "twin": {
        "concept_mastery": {"integration_by_parts": 0.30},
    },
    "intent": "concept_explanation",
    "student_message": "How do I integrate x times e^x?",
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO E3 — the flag test
# ─────────────────────────────────────────────────────────────────────────────
# The briefing is about STATISTICS. The student asks about MATRICES. Whatever
# the Coach produces cannot be grounded in this briefing — the evidence is
# about a different subject entirely.
SCENARIO_E3 = {
    "name": "E3 — Ungroundable (flag should fire)",
    "what_to_watch": (
        "1. The briefing is entirely about statistics. The question is about\n"
        "   matrices. Nothing in the evidence can account for the reply.\n"
        "2. EXPECTED: exactly 'flag: evidence_insufficient' and nothing else.\n"
        "   No record, no rationale, no explanation of the flag.\n"
        "3. If it produces a confident record instead, the gate never fires\n"
        "   and the whole verification idea is decorative.\n"
        "4. If it emits the flag AND a record, the 'nothing else' instruction\n"
        "   is not holding — a parser would then have to handle both."
    ),
    "twin": {
        "learning_style": "formal",
        "concept_mastery": {"hypothesis_testing": 0.40, "p_values": 0.35},
        "recent_errors": ["confused p-value with probability of the null"],
    },
    "intent": "concept_explanation",
    "student_message": "How do I multiply two matrices?",
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO E4 — anti-over-fire
# ─────────────────────────────────────────────────────────────────────────────
# The mirror of E3, and the more important of the two. The briefing grounds the
# reply perfectly well, but the Coach will likely produce something long and
# unusual — the misconception strategy: surface the wrong belief, break it with
# a counterexample, rebuild.
#
# A gate that fires on "this looks odd" rather than "this is ungrounded" fills
# the log with false alarms and makes the groundability metric meaningless.
SCENARIO_E4 = {
    "name": "E4 — Unusual but grounded (flag must NOT fire)",
    "what_to_watch": (
        "1. THE FALSE-ALARM TEST. The Coach will attack a misconception with a\n"
        "   counterexample — long, unusual, possibly a strange analogy.\n"
        "2. It is GROUNDED: the briefing names the misconception explicitly.\n"
        "3. NO FLAG. If the flag fires here, the gate is judging quality\n"
        "   instead of grounding, and the anti-over-fire rule is too weak.\n"
        "4. The record should cite the known misconception as the reason for\n"
        "   the counterexample approach."
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {"product_rule": 0.25},
        "known_misconceptions": [
            "believes the derivative of a product is the product of the derivatives"
        ],
    },
    "intent": "answer_check",
    "student_message": "The derivative of x^2 * sin(x) is 2x * cos(x), right?",
}


SCENARIOS = [
    SCENARIO_E1,
    SCENARIO_E2,
    SCENARIO_E3,
    SCENARIO_E4,
]

for scenario in SCENARIOS:
    run_scenario(scenario)