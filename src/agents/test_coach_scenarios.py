"""
Scenario test harness for the Study Coach agent.

Runs the Coach against several mock Twins that exercise branches the happy-path
test never reached: a genuine GAP, a WRONG student, a different learning style,
and evidence that reverses direction mid-session.

Each scenario prints what to watch for before its output, so results can be
judged against the prompt's own rules rather than by general impression.

Run from the project root:
    python src/agents/test_coach_scenarios.py

To run only some scenarios, comment out entries in SCENARIOS at the bottom.
"""

from google import genai
from google.genai import types

client = genai.Client()  # reads GEMINI_API_KEY from the environment

MODEL = "gemini-3.6-flash"

system_prompt = open(
    "src/agents/prompts/coach_system_v3.txt", encoding="utf-8"
).read()


def build_briefing(t):
    """Render the Twin slice as the text for the <briefing> slot.

    Fields that are empty or absent are omitted entirely. A line reading
    "Known misconceptions: " with nothing after it is noise, and worse, invites
    the model to treat an empty field as meaningful.
    """
    lines = [f"Learning style: {t['learning_style']}"]

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
    """Replay one scripted conversation and print the Coach's replies."""
    print(f"\n\n{'#' * 78}")
    print(f"# SCENARIO {scenario['name']}")
    print(f"{'#' * 78}")
    print(f"\nWHAT TO WATCH:\n{scenario['what_to_watch']}\n")

    twin = scenario["twin"]
    history = []

    for turn_index, student_question in enumerate(scenario["turns"], start=1):

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
{scenario['intent']}
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

        history.append(f"Student: {student_question}")
        history.append(f"Coach: {reply}")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO A — a genuine GAP (no misconception anywhere)
# ─────────────────────────────────────────────────────────────────────────────
# The concept is simply missing: near-zero mastery, no wrong belief, nothing in
# recent_errors. Step 2 of the prompt says gaps are handled by BUILDING UP from
# the weakest prerequisite — not by surfacing and breaking a belief. A weak
# prerequisite (integration_basic = 0.30) is planted so step 3 has something to
# anchor on.
SCENARIO_A = {
    "name": "A — Gap case (concept missing, no misconception)",
    "what_to_watch": (
        "1. Does it BUILD UP from a prerequisite, or does it attack a\n"
        "   misconception that does not exist?\n"
        "2. Does it anchor on integration_basic (0.30, the weak prerequisite)\n"
        "   before the target concept, as step 3 requires?\n"
        "3. Does a gap_confirmed signal appear? It never has before.\n"
        "4. Confidence should sit in the WEAKNESS band (0.5-0.7 for a single\n"
        "   clear instance), not the competence band."
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {
            "derivatives": 0.80,
            "product_rule": 0.75,
            "integration_basic": 0.30,
            "integration_by_parts": 0.05,
        },
        "recent_errors": [],
        "known_misconceptions": [],
    },
    "intent": "concept_explanation",
    "turns": [
        "How do I integrate x times e^x? I've never seen this type before.",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO B — a WRONG student, misconception NOT pre-flagged
# ─────────────────────────────────────────────────────────────────────────────
# The classic error: treating the derivative of a product as the product of the
# derivatives. Nothing in the briefing warns about it, so the Coach must detect
# it from the student's own words — the second half of step 1's DIAGNOSE rule,
# which has never been exercised.
SCENARIO_B = {
    "name": "B — Wrong student (misconception revealed, not pre-flagged)",
    "what_to_watch": (
        "1. Does it CATCH the error at all, given the briefing says nothing?\n"
        "2. Does it follow the misconception strategy: surface the wrong belief,\n"
        "   break it with a COUNTEREXAMPLE, then rebuild?\n"
        "3. Does misconception_detected fire? It never has before.\n"
        "4. Confidence should be 0.5-0.7 (single clear instance of a wrong\n"
        "   belief), NOT the 0.8+ band.\n"
        "5. It must NOT emit briefing_contradicted — the briefing said nothing\n"
        "   to contradict."
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {
            "derivatives": 0.70,
            "product_rule": 0.25,
            "chain_rule": 0.65,
        },
        "recent_errors": [],
        "known_misconceptions": [],
    },
    "intent": "answer_check",
    "turns": [
        "The derivative of x^2 * sin(x) is 2x * cos(x), right?",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO C — learning style flipped to formal
# ─────────────────────────────────────────────────────────────────────────────
# Identical to the original happy-path turn 1 in every respect EXCEPT
# learning_style. Compare directly against the run already captured. If the two
# responses are shaped the same, that briefing field is decorative — which
# matters, since personalisation is the project's central claim.
SCENARIO_C = {
    "name": "C — Learning style = formal (compare against example-driven run)",
    "what_to_watch": (
        "Compare the SHAPE of the reply against the earlier example-driven run\n"
        "of this exact turn.\n"
        "  formal        -> definition or rule stated FIRST\n"
        "  example-driven-> concrete scenario FIRST\n"
        "If the two replies open the same way, <briefing> learning_style is not\n"
        "changing behaviour and that is a finding worth recording."
    ),
    "twin": {
        "learning_style": "formal",
        "concept_mastery": {
            "limits": 0.85,
            "derivatives": 0.35,
            "chain_rule": 0.20,
        },
        "recent_errors": [
            "differentiated sin(2x) as cos(2x), dropping the inner derivative"
        ],
        "known_misconceptions": [
            "thinks the chain rule is optional when the inside looks simple"
        ],
    },
    "intent": "concept_explanation",
    "turns": [
        "For sin(2x) I take cos(2x) and multiply by the derivative of the "
        "inside, which is 2, so 2cos(2x) — right?",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO D — evidence that REVERSES direction mid-session
# ─────────────────────────────────────────────────────────────────────────────
# Two correct answers on linear inner functions, then a failure on a non-linear
# one. This is the case the supersession proposal assumes away: within-session
# evidence is presumed to refine in one direction. Here it does not.
SCENARIO_D = {
    "name": "D — Competence then failure (evidence reverses mid-session)",
    "what_to_watch": (
        "1. On turn 3, does it emit BOTH mastery_evidence (turns 1-2) and a\n"
        "   weakness signal, or does the failure erase the earlier competence?\n"
        "2. Does the turn-3 confidence DROP, and is that coherent with the\n"
        "   turn-2 signal it supposedly refines?\n"
        "3. Does it use the same concept label 'chain_rule' for both the\n"
        "   competence and the failure? If so, the Twin receives contradictory\n"
        "   claims about one node — the granularity problem, made concrete.\n"
        "4. Critical for the report: if a later signal does NOT re-cite the\n"
        "   earlier evidence, supersession would DISCARD it rather than refine\n"
        "   it. Check whether turn 3 still cites turns 1-2."
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {
            "limits": 0.85,
            "derivatives": 0.35,
            "chain_rule": 0.20,
        },
        "recent_errors": [
            "differentiated sin(2x) as cos(2x), dropping the inner derivative"
        ],
        "known_misconceptions": [
            "thinks the chain rule is optional when the inside looks simple"
        ],
    },
    "intent": "answer_check",
    "turns": [
        "For sin(2x) I get 2cos(2x) — multiply by the derivative of the inside.",
        "And sin(5x) would be 5cos(5x).",
        "So sin(x^2) is 2cos(x^2)... wait, or is it just cos(x^2)?",
    ],
}
# (Comment out A-D so you only re-run the new ones.)
# ─────────────────────────────────────────────────────────────────────────────
 
 
# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO E — the REVERSE contradiction: record says strong, student is wrong
# ─────────────────────────────────────────────────────────────────────────────
# Every contradiction observed so far has been GOOD news: the record understated
# the student. This is the mirror case — the record OVERSTATES them. Structurally
# identical (two true observations at once), so it should produce two blocks. If
# it produces only one, the Coach reports contradictions asymmetrically, which
# would mean the Twin can inflate beliefs easily but not correct them downward.
SCENARIO_E = {
    "name": "E — Record says strong, student is wrong (reverse contradiction)",
    "what_to_watch": (
        "1. Does it emit TWO signals — briefing_contradicted AND a weakness\n"
        "   signal (misconception_detected or gap_confirmed)?\n"
        "2. If it emits only the weakness signal, the Twin never learns its\n"
        "   0.90 mastery record is wrong. That is an ASYMMETRY: contradictions\n"
        "   reported when they flatter the student, suppressed when they do not.\n"
        "3. Does it still teach correctly despite the briefing saying 'skip the\n"
        "   basics, go subtle' (step 3, high mastery)? Or does the inflated\n"
        "   record make it pitch over the student's head?\n"
        "4. Confidence on the contradiction should be 0.7-0.8 (single clear\n"
        "   instance)."
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {
            "limits": 0.85,
            "derivatives": 0.88,
            "chain_rule": 0.90,
        },
        "recent_errors": [],
        "known_misconceptions": [],
    },
    "intent": "answer_check",
    "turns": [
        "The derivative of sin(4x) is cos(4x), right? The 4 doesn't change anything.",
    ],
}
 
 
# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO F — step 3 anchoring, retested with a starker weakness
# ─────────────────────────────────────────────────────────────────────────────
# Scenario A did NOT anchor on the weak prerequisite (integration_basic = 0.30);
# it went straight to the target concept. Two explanations: the rule is being
# ignored, or 0.30 was not weak enough to trigger it. This isolates that by
# making the prerequisite unmistakably weak (0.10) and unmistakably load-bearing
# — you cannot do integration by parts without knowing basic antiderivatives.
# If it STILL skips the prerequisite, step 3 needs rewording.
SCENARIO_F = {
    "name": "F — Step 3 anchoring retest (prerequisite at 0.10)",
    "what_to_watch": (
        "1. Does it now anchor on integration_basic (0.10) BEFORE teaching\n"
        "   integration by parts, as step 3 requires?\n"
        "2. Or does it again jump to the target concept and silently assume\n"
        "   the student can integrate e^x?\n"
        "3. If it skips the prerequisite at 0.10, step 3 is not being followed\n"
        "   and the rule needs rewording — not the scenario.\n"
        "4. Does it emit a gap signal for the PREREQUISITE as well as the\n"
        "   target concept, or only the target?"
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {
            "derivatives": 0.80,
            "product_rule": 0.75,
            "integration_basic": 0.10,
            "integration_by_parts": 0.05,
        },
        "recent_errors": [
            "could not evaluate the integral of e^x; left it unanswered"
        ],
        "known_misconceptions": [],
    },
    "intent": "concept_explanation",
    "turns": [
        "How do I integrate x times e^x? I've never seen this type before.",
    ],
}
 
 
# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO G — do granular concept labels follow the briefing?
# ─────────────────────────────────────────────────────────────────────────────
# In A and B the Coach reused the exact concept keys from the briefing
# (integration_by_parts, product_rule) rather than inventing labels. If that
# holds, splitting a concept in the briefing should split the signals too —
# which is the knowledge-graph plan tested cheaply, with no prompt change.
#
# Same three turns as scenario D, but chain_rule is now TWO keys. Watch whether
# the competence signals attach to the linear node and the failure to the
# composite one.
SCENARIO_G = {
    "name": "G — Granular concept keys (chain_rule split into two nodes)",
    "what_to_watch": (
        "1. Do turns 1-2 label the signal 'chain_rule_linear' rather than a\n"
        "   generic 'chain_rule'?\n"
        "2. Does turn 3 label the failure 'chain_rule_composite'?\n"
        "3. If yes: granularity is controlled entirely by what RETRIEVAL sends,\n"
        "   with no prompt change needed. The Twin's graph shape propagates to\n"
        "   the signals for free.\n"
        "4. If it collapses both to one label anyway, the prompt needs an\n"
        "   explicit rule about reusing briefing keys."
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {
            "limits": 0.85,
            "derivatives": 0.35,
            "chain_rule_linear": 0.20,
            "chain_rule_composite": 0.10,
        },
        "recent_errors": [
            "differentiated sin(2x) as cos(2x), dropping the inner derivative"
        ],
        "known_misconceptions": [
            "thinks the chain rule is optional when the inside looks simple"
        ],
    },
    "intent": "answer_check",
    "turns": [
        "For sin(2x) I get 2cos(2x) — multiply by the derivative of the inside.",
        "And sin(5x) would be 5cos(5x).",
        "So sin(x^2) is 2cos(x^2)... wait, or is it just cos(x^2)?",
    ],
}
SCENARIO_H = {
    "name": "H — Learning style = visual",
    "what_to_watch": (
        "1. Does it actually DESCRIBE A PICTURE or diagram, as step 2 requires\n"
        "   for visual learners?\n"
        "2. Compare the opening against the other two runs of this same turn:\n"
        "     example-driven -> walked through the student's own numbers\n"
        "     formal         -> stated f'(g(x))·g'(x) first\n"
        "     visual         -> should describe something SEEN, not just told\n"
        "3. If it looks like the example-driven reply, 'visual' is not being\n"
        "   honoured and only two of your three styles actually work."
    ),
    "twin": {
        "learning_style": "visual",
        "concept_mastery": {
            "limits": 0.85,
            "derivatives": 0.35,
            "chain_rule": 0.20,
        },
        "recent_errors": [
            "differentiated sin(2x) as cos(2x), dropping the inner derivative"
        ],
        "known_misconceptions": [
            "thinks the chain rule is optional when the inside looks simple"
        ],
    },
    "intent": "concept_explanation",
    "turns": [
        "For sin(2x) I take cos(2x) and multiply by the derivative of the "
        "inside, which is 2, so 2cos(2x) — right?",
    ],
}
 
 
# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO I — confusion_resolved (the enum value that has never fired)
# ─────────────────────────────────────────────────────────────────────────────
# Turn 1 the student states confusion openly. Turn 2, after the Coach's reply,
# they work it out correctly. That second turn is exactly what
# confusion_resolved describes — and nothing in testing has ever produced it.
SCENARIO_I = {
    "name": "I — Confusion then resolution",
    "what_to_watch": (
        "TURN 1: expect a weakness signal (gap_confirmed on\n"
        "  chain_rule_composite). The student states confusion, not a wrong\n"
        "  belief, so misconception_detected would be the wrong label.\n"
        "TURN 2: does confusion_resolved fire? It never has.\n"
        "  If it emits mastery_evidence instead, ask whether the two labels are\n"
        "  distinguishable at all — if not, one of them is dead weight in the\n"
        "  enum.\n"
        "  Confidence should be in the competence band (0.5-0.7: mechanism\n"
        "  explained once)."
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {
            "derivatives": 0.70,
            "chain_rule_linear": 0.75,
            "chain_rule_composite": 0.15,
            "power_rule": 0.80,
        },
        "recent_errors": [],
        "known_misconceptions": [],
    },
    "intent": "concept_explanation",
    "turns": [
        "I don't get why sin(x^2) isn't just cos(x^2). Where does the extra "
        "bit even come from?",
        "Oh — so the inside is x^2, and its derivative is 2x, so the answer is "
        "2x·cos(x^2)?",
    ],
}
 
 
# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO J — over-firing check for mastery_unstable
# ─────────────────────────────────────────────────────────────────────────────
# THE MOST IMPORTANT NEW TEST. The prompt says hesitation that LANDS ON THE
# RIGHT ANSWER is NOT instability — it should stay mastery_evidence with lowered
# confidence. Here the student wavers out loud and then corrects themselves to
# the correct answer.
#
# If mastery_unstable fires here, the new signal is over-applying exactly as
# predicted, and its trigger rule needs tightening.
SCENARIO_J = {
    "name": "J — Hesitation that lands correct (mastery_unstable must NOT fire)",
    "what_to_watch": (
        "TURN 2 is the whole test.\n"
        "  CORRECT: mastery_evidence, confidence at the LOWER end of its band,\n"
        "    with the hesitation noted in 'detail'.\n"
        "  WRONG: mastery_unstable. The student never committed to a wrong\n"
        "    answer and never left two answers standing — they self-corrected\n"
        "    and landed right. If it fires, the trigger rule is too loose.\n"
        "Also check: does 'detail' actually mention the hesitation, as the\n"
        "  lowering rule requires?"
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {
            "derivatives": 0.60,
            "chain_rule_linear": 0.55,
            "chain_rule_composite": 0.20,
        },
        "recent_errors": [],
        "known_misconceptions": [],
    },
    "intent": "answer_check",
    "turns": [
        "For sin(2x) I get 2cos(2x) — multiply by the derivative of the inside.",
        "Now sin(x^2)... hmm, is it just cos(x^2)? No wait — the inside is x^2 "
        "and its derivative is 2x, so it's 2x·cos(x^2).",
    ],
}
 
 
# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO K — stability: same input, three times
# ─────────────────────────────────────────────────────────────────────────────
# Every scenario so far has been run ONCE. That cannot tell you whether the
# confidence numbers are reliable or just one lucky draw. Models are not
# deterministic, so identical input can produce different output.
#
# HOW TO RUN: put this scenario in the SCENARIOS list three times:
#     SCENARIOS = [SCENARIO_K, SCENARIO_K, SCENARIO_K]
# Then compare the three results.
SCENARIO_K = {
    "name": "K — Stability check (run this one THREE times)",
    "what_to_watch": (
        "Compare the three runs against each other:\n"
        "1. Same signal TYPES each time, or do they vary?\n"
        "2. Same concept LABEL each  time?\n"
        "3. How far apart are the confidence numbers?\n"
        "     within ~0.1  -> the field is usable for Twin thresholds\n"
        "     0.3+ apart   -> too noisy to drive a threshold; treat it as a\n"
        "                     coarse weak/moderate/strong band instead\n"
        "This is the evidence for or against §3 of the interface report, which\n"
        "currently warns the Twin team not to trust the number precisely."
    ),
    "twin": {
        "learning_style": "example-driven",
        "concept_mastery": {
            "limits": 0.85,
            "derivatives": 0.35,
            "chain_rule": 0.20,
        },
        "recent_errors": [
            "differentiated sin(2x) as cos(2x), dropping the inner derivative"
        ],
        "known_misconceptions": [
            "thinks the chain rule is optional when the inside looks simple"
        ],
    },
    "intent": "answer_check",
    "turns": [
        "For sin(2x) I get 2cos(2x) — multiply by the derivative of the inside.",
    ],
}

# Comment out any scenario you do not want to run.
SCENARIOS = [
    SCENARIO_A,
    SCENARIO_B,
    #SCENARIO_C,
    #SCENARIO_D,
    #SCENARIO_E,
    #SCENARIO_F,
    #SCENARIO_G
    #SCENARIO_H,
    SCENARIO_I,
    #SCENARIO_J,
    #SCENARIO_K,

]



for scenario in SCENARIOS:
    run_scenario(scenario)