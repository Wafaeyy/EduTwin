from google import genai
from google.genai import types

client = genai.Client()  # reads GEMINI_API_KEY from your environment

# static recipe: the file you already wrote
system_prompt = open("src/agents/prompts/coach_system_v1.txt", encoding="utf-8").read()

# mock Twin: stand-in until the real Twin is live
twin = {
    "learning_style": "example-driven",
    "concept_mastery": {"limits": 0.85, "derivatives": 0.35, "chain_rule": 0.20},
    "recent_errors": ["differentiated sin(2x) as cos(2x), dropping the inner derivative"],
    "known_misconceptions": ["thinks the chain rule is optional when the inside looks simple"],
}

def build_briefing(t):
    return "\n".join([
        f"Learning style: {t['learning_style']}",
        "Concept mastery (0-1): " + ", ".join(f"{k}={v}" for k, v in t["concept_mastery"].items()),
        "Recent errors: " + "; ".join(t["recent_errors"]),
        "Known misconceptions: " + "; ".join(t["known_misconceptions"]),
    ])

intent = "concept_explanation"          # stub until the intent classifier exists
student_question = "For sin(2x) I take cos(2x) and multiply by the derivative of the inside, which is 2, so 2cos(2x) — right?"

user_block = f"""<student_message>
{student_question}
</student_message>

<intent>
{intent}
</intent>

<briefing>
{build_briefing(twin)}
</briefing>"""

resp = client.models.generate_content(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(system_instruction=system_prompt),
    contents=user_block,
)

print(resp.text)