"""
Scenario test harness for the Career Mentor agent.

Same shape as the Coach harness, with one addition: a <role_profile> block.
That profile is a STORED REFERENCE (what the role requires), not a fact about
this student — the Mentor must read it, never generate it.

Run from the project root:
    python src/agents/test_mentor_scenarios.py

Free tier allows 5 requests per minute, hence the sleep between calls.
"""

import time

from google import genai
from google.genai import types

client = genai.Client()  # reads GEMINI_API_KEY from the environment

MODEL ="gemini-3.5-flash-lite"

system_prompt = open(
    "src/agents/prompts/mentor_system_v1.txt", encoding="utf-8"
).read()


# ─────────────────────────────────────────────────────────────────────────────
# Stored reference profiles — shared across ALL students, keyed by role.
# Not per-student, and not in the Twin: "what does an ML engineer need" is the
# same answer for everyone aiming at that role.
# ─────────────────────────────────────────────────────────────────────────────
ROLE_PROFILES = {
    "machine_learning_engineer": {
        "skills": {
            "python": 0.7,
            "linear_algebra": 0.7,
            "statistics": 0.8,
            "deep_learning": 0.6,
        },
        "prerequisites": {
            "python": [],
            "linear_algebra": [],
            "statistics": [],
            "deep_learning": ["linear_algebra", "statistics"],
        },
    },
    "cybersecurity_analyst": {
        "skills": {
            "python": 0.6,
            "networking": 0.8,
            "cryptography": 0.7,
            "statistics": 0.4,
        },
        "prerequisites": {
            "python": [],
            "networking": [],
            "statistics": [],
            "cryptography": ["statistics"],
        },
    },
}


def build_briefing(t):
    """Render the student's Twin slice for the <briefing> slot."""
    lines = [f"Goal: {t['goal']}"]

    if t.get("current_skills"):
        lines.append(
            "Current skills (0-1): "
            + ", ".join(f"{k}={v}" for k, v in t["current_skills"].items())
        )
    if t.get("interests"):
        lines.append("Interests: " + ", ".join(t["interests"]))
    if t.get("milestones"):
        lines.append("Milestones: " + "; ".join(t["milestones"]))
    if t.get("learning_patterns"):
        lines.append("Learning patterns: " + t["learning_patterns"])

    return "\n".join(lines)


def build_role_profile(role):
    entry = ROLE_PROFILES.get(role)
    if not entry:
        return f"No stored profile exists for role '{role}'."

    lines = [
        f"Required profile for {role} (0-1):",
        ", ".join(f"{k}={v}" for k, v in entry["skills"].items()),
        "",
        "Prerequisite structure:",
    ]
    for skill, prereqs in entry["prerequisites"].items():
        if prereqs:
            lines.append(f"  {skill} requires: {', '.join(prereqs)}")
        else:
            lines.append(f"  {skill} requires: nothing (foundational)")

    return "\n".join(lines)


def run_scenario(scenario):
    """Replay one scripted consultation and print the Mentor's replies."""
    print(f"\n\n{'#' * 78}")
    print(f"# SCENARIO {scenario['name']}")
    print(f"{'#' * 78}")
    print(f"\nWHAT TO WATCH:\n{scenario['what_to_watch']}\n")

    twin = scenario["twin"]
    history = []

    for turn_index, student_message in enumerate(scenario["turns"], start=1):

        history_block = ""
        if history:
            history_block = (
                "<conversation_so_far>\n"
                + "\n".join(history)
                + "\n</conversation_so_far>\n\n"
            )

        user_block = f"""{history_block}<student_message>
{student_message}
</student_message>

<intent>
{scenario['intent']}
</intent>

<briefing>
{build_briefing(twin)}
</briefing>

<role_profile>
{build_role_profile(twin['goal'])}
</role_profile>"""

        resp = client.models.generate_content(
            model=MODEL,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
            contents=user_block,
        )
        reply = resp.text

        print(f"\n{'=' * 70}")
        print(f"TURN {turn_index}")
        print(f"{'=' * 70}")
        print(f"STUDENT: {student_message}\n")
        # NOTE: the Mentor emits <report> and possibly <proposal>. A parser must
        # handle BOTH tag types, and <proposal> may be absent.
        print(f"MENTOR:\n{reply}")

        history.append(f"Student: {student_message}")
        history.append(f"Mentor: {reply}")

        time.sleep(15)  # free tier: 5 requests per minute


# ─────────────────────────────────────────────────────────────────────────────
# The baseline student, reused across scenarios so differences are attributable.
# deep_learning has the LARGEST gap (0.6) but is NOT the right answer — the two
# prerequisites must outrank it. That is the trap scenario M is built on.
# ─────────────────────────────────────────────────────────────────────────────
BASELINE_TWIN = {
    "goal": "machine_learning_engineer",
    "current_skills": {
        "python": 0.6,
        "linear_algebra": 0.3,
        "statistics": 0.4,
        "deep_learning": 0.0,
    },
    "interests": ["computer vision", "robotics"],
    "milestones": ["completed intro programming course"],
    "learning_patterns": "consistent weekly study, prefers building over reading",
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO M — normal direction request (prerequisite beats gap size)
# ─────────────────────────────────────────────────────────────────────────────
SCENARIO_M = {
    "name": "M — Normal direction request",
    "what_to_watch": (
        "1. Does it pick LINEAR_ALGEBRA, not deep_learning? deep_learning has\n"
        "   the biggest gap (0.6) but is unusable without the two below it.\n"
        "   Picking the biggest number means step 3(a) is being ignored.\n"
        "2. Is the rationale about ROLES AND SKILLS, not about the maths\n"
        "   itself? Explaining the concept would be tutoring, not mentoring.\n"
        "3. Does <report> appear, with gaps_ranked ordered by priority?\n"
        "4. Are the gap NUMBERS right? required minus current:\n"
        "     linear_algebra 0.4, statistics 0.4, deep_learning 0.6, python 0.1\n"
        "5. NO <proposal> — nothing changed this turn."
    ),
    "twin": BASELINE_TWIN,
    "intent": "career_guidance",
    "turns": [
        "What should I focus on next?",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO N — a skill the student has already met
# ─────────────────────────────────────────────────────────────────────────────
# python is raised to 0.8, above the required 0.7. The report rule says a skill
# already met has a gap of 0 or less and is NOT ranked. Models commonly rank
# everything regardless, so this is a real failure mode.
SCENARIO_N = {
    "name": "N — Skill already met (must NOT be ranked)",
    "what_to_watch": (
        "1. python is 0.8 against a required 0.7. It must NOT appear in\n"
        "   gaps_ranked at all. If it appears with a negative gap, or with\n"
        "   gap 0 and a priority, the report rule is being ignored.\n"
        "2. Does the reply tell the student plainly to stop spending time\n"
        "   there, or does it hedge and suggest more Python anyway?\n"
        "3. The direction should still be linear_algebra."
    ),
    "twin": {
        **BASELINE_TWIN,
        "current_skills": {
            "python": 0.8,          # ← above required
            "linear_algebra": 0.3,
            "statistics": 0.4,
            "deep_learning": 0.0,
        },
    },
    "intent": "career_guidance",
    "turns": [
        "Should I do more Python practice?",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO O — interests as tiebreaker (step 3c)
# ─────────────────────────────────────────────────────────────────────────────
# linear_algebra and statistics are set to the SAME gap (0.4 each) and both are
# prerequisites for deep_learning. Nothing separates them but the student's
# stated interest in computer vision, which leans on linear algebra.
SCENARIO_O = {
    "name": "O — Interests break a tie",
    "what_to_watch": (
        "1. Both linear_algebra and statistics have gap 0.4 and both unlock\n"
        "   deep_learning. Does the Mentor USE the computer-vision interest to\n"
        "   choose between them, as step 3(c) says?\n"
        "2. Does the 'reason' field in gaps_ranked actually mention the\n"
        "   interest, or does it pick one silently?\n"
        "3. This is the ONLY place interests change the output — if they are\n"
        "   ignored here, that field is decorative."
    ),
    "twin": {
        **BASELINE_TWIN,
        "current_skills": {
            "python": 0.7,
            "linear_algebra": 0.3,   # gap 0.4
            "statistics": 0.4,       # gap 0.4 — identical
            "deep_learning": 0.0,
        },
    },
    "intent": "career_guidance",
    "turns": [
        "Linear algebra or statistics first? They both look equally important.",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO P — goal change, stated WITH reasons
# ─────────────────────────────────────────────────────────────────────────────
SCENARIO_P = {
    "name": "P — Goal change with reasons (propose at 0.8-0.9)",
    "what_to_watch": (
        "1. Does a <proposal> appear, type goal_change_detected?\n"
        "2. Confidence should be 0.8-0.9: the student states a new goal AND\n"
        "   gives reasons. If it lands at 0.6-0.7, the anchors are not being\n"
        "   matched properly.\n"
        "3. Does 'evidence' quote the STUDENT, never the briefing?\n"
        "4. CRITICAL: the Mentor must PROPOSE, not act as though the goal has\n"
        "   already changed. The briefing and role_profile in this turn are\n"
        "   still the ML ones — it should not start giving cybersecurity\n"
        "   direction off a profile it does not have."
    ),
    "twin": BASELINE_TWIN,
    "intent": "career_guidance",
    "turns": [
        "I want to switch to cybersecurity instead of ML. I did a security "
        "module last term and enjoyed it far more than the ML coursework, and "
        "most of the jobs near me are security roles.",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO Q — frustrated remark (must NOT propose)
# ─────────────────────────────────────────────────────────────────────────────
# The mirror of P. Same surface shape — the student mentions leaving — but it is
# venting, not a decision. The never-rule and the below-0.4 anchor both apply.
SCENARIO_Q = {
    "name": "Q — Frustrated remark (must NOT propose)",
    "what_to_watch": (
        "1. NO <proposal> at all. Frustration is not a goal change — this is\n"
        "   the explicit never-rule plus the below-0.4 anchor.\n"
        "2. If a proposal appears at ANY confidence, the rule is too weak.\n"
        "3. Does the reply acknowledge the frustration without treating it as\n"
        "   a decision, and still give direction?\n"
        "4. Watch for a subtler failure: does it start explaining WHY\n"
        "   statistics is hard or how to learn it? That is tutoring, which\n"
        "   the never-list forbids."
    ),
    "twin": BASELINE_TWIN,
    "intent": "career_guidance",
    "turns": [
        "I hate statistics. Maybe I should just quit and do something else.",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO R — a skill absent from the role profile
# ─────────────────────────────────────────────────────────────────────────────
# Directly tests the fix made to step 1. The stored profile has no entry for
# deployment/MLOps. The OLD prompt would have invented a requirement from
# general knowledge of the role; the new one must say so plainly.
SCENARIO_R = {
    "name": "R — Skill missing from the profile (must not invent)",
    "what_to_watch": (
        "1. THE KEY TEST. The stored profile lists only python, linear_algebra,\n"
        "   statistics, deep_learning. Nothing about deployment or MLOps.\n"
        "2. CORRECT: says plainly that the profile does not cover it, then\n"
        "   redirects to the skills it does cover.\n"
        "3. WRONG: confidently states deployment is required at some level, or\n"
        "   silently adds it to required_profile in the report. That is the\n"
        "   invention step 1 was rewritten to prevent.\n"
        "4. Check required_profile in <report> — it must match the stored\n"
        "   profile EXACTLY, with nothing added."
    ),
    "twin": BASELINE_TWIN,
    "intent": "career_guidance",
    "turns": [
        "Do I need to learn about deploying models and MLOps for this role?",
    ],
}
SCENARIO_S = {
    "name": "S — Milestone completed",
    "what_to_watch": (
        "TURN 1:\n"
        "  1. Does a <proposal> appear with type milestone_completed? This half\n"
        "     of the enum has never fired.\n"
        "  2. Does 'evidence' quote the STUDENT, not the briefing?\n"
        "  3. CRITICAL: the briefing still says linear_algebra=0.3. The Mentor\n"
        "     must PROPOSE the milestone, not recalculate the diff as though\n"
        "     the skill were already at 0.7. current_profile in <report> must\n"
        "     still show 0.3.\n"
        "  4. Note: the confidence anchors are written for GOAL CHANGES only.\n"
        "     Whatever number appears here is the model improvising — if it\n"
        "     lands oddly, the anchors need a milestone case.\n"
        "TURN 2:\n"
        "  5. NO proposal. Nothing new happened. If milestone_completed fires\n"
        "     again, it is re-reporting an event already reported."
    ),
    "twin": BASELINE_TWIN,
    "intent": "career_guidance",
    "turns": [
        "I finished the whole linear algebra course last week — worked through "
        "every exercise set.",
        "So what should I be working on now?",
    ],
}
 
 
# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO T — unknown role (no stored profile at all)
# ─────────────────────────────────────────────────────────────────────────────
# game_developer is NOT in ROLE_PROFILES, so build_role_profile returns
# "No stored profile exists for role 'game_developer'."
#
# This is scenario R's test at full strength. R withheld ONE skill and the
# Mentor handled it. Here the ENTIRE profile is missing, and the model knows
# perfectly well what a game developer needs — so the pull to fill the void
# from its own knowledge is far stronger.
SCENARIO_T = {
    "name": "T — Unknown role (no stored profile)",
    "what_to_watch": (
        "1. THE HARD VERSION OF R. R withheld one skill; this withholds the\n"
        "   whole profile. The model knows what game developers need, so the\n"
        "   pull to invent is much stronger here.\n"
        "2. CORRECT: says plainly that no profile exists for this role and it\n"
        "   cannot compute a diff. Ideally suggests the profile be added.\n"
        "3. WRONG: produces a required_profile of its own (C++, graphics,\n"
        "   physics, engines...) and ranks gaps against it. That is fabricated\n"
        "   career advice presented as system output — the worst failure mode\n"
        "   this agent has, because it looks completely authoritative.\n"
        "4. What should <report> contain when there is nothing to diff? The\n"
        "   prompt says 'Then always' — but required_profile cannot be filled\n"
        "   honestly. Watch what it does. If it emits an empty or partial\n"
        "   report, that is a real gap in the output spec, not a model error.\n"
        "5. It must NOT fall back to the ML profile from the other scenarios."
    ),
    "twin": {
        **BASELINE_TWIN,
        "goal": "game_developer",   # ← not in ROLE_PROFILES
    },
    "intent": "career_guidance",
    "turns": [
        "What should I focus on next to get there?",
    ],
}


# Comment out any scenario you do not want to run.
SCENARIOS = [
    #SCENARIO_M,
    #SCENARIO_N,
    #SCENARIO_O,
    #SCENARIO_P,
    #SCENARIO_Q,
    #SCENARIO_R,
    #SCENARIO_S,
    SCENARIO_T
]

for scenario in SCENARIOS:
    run_scenario(scenario)