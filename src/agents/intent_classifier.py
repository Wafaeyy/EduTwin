import json
import re

from google import genai
from google.genai import types

from src.agents.schemas import AgentType, IntentDecision


class IntentClassifier:
    """
    Classifies student queries into specific agent domains and intent categories.
    """

    def __init__(
        self,
        model: str = "gemini-3.6-flash",
        client: genai.Client | None = None,
        api_key: str | None = None,
    ):
        self.model = model
        self.client = client or genai.Client(api_key=api_key)

    def classify(
        self,
        query: str,
        context_summary: str | None = None,
        history: list[str] | None = None,
    ) -> IntentDecision:
        """
        Classifies the student query into an AgentType and specific intent.

        Args:
            query: The current student question or statement.
            context_summary: Optional context/briefing summary to assist classification.

        Returns:
            IntentDecision with the target agent, canonical intent, confidence, and rationale.
        """
        prompt = f"""
You are the Intent Classifier and Router for EduTwin, a personalized educational AI platform.

Analyze the user's message and determine which specialized AI Agent should handle it, along with the canonical intent.

### AVAILABLE AGENTS & INTENTS:

1. Agent: "study_coach" (Academic Tutoring & Concept Learning)
   - "explain_concept": Student asks for an explanation of a concept, theory, formula, mechanism, or how something works.
   - "check_answer": Student shares an answer, calculation, or line of reasoning and asks to verify if it is correct.
   - "give_practice": Student asks for exercises, practice questions, or problems to solve.

2. Agent: "career_mentor" (Career Planning, Skills, & Long-Term Goals)
   - "career_fit_question": Student asks if a career path, role, or direction suits them or what skills a role needs.
   - "progress_alignment_check": Student asks what to study next in the long run or if they are on track for their career goal.
   - "goal_change": Student expresses interest in becoming a specific role, changing their primary career goal, or changing learning direction.

3. Agent: "recommendation_system" (External Learning Resources)
   - "resource_recommendation": Student specifically asks for videos, courses, books, links, or articles to learn something.

4. Agent: "explainability" (System Transparency)
   - "explain_decision": Student asks WHY the system recommended a specific item, gave specific advice, or made a decision.
   ##Ouptut format

### USER MESSAGE:
\"\"\"{query}\"\"\"

### HOW TO CHOOSE
- If the message asks about a concept, an answer, or practice, it is study_coach.
- If it asks about a career, a role, long-term direction, or changing goals, it
  is career_mentor.
- If it asks for specific materials to learn from, it is recommendation_system.
- If it asks why the system said or suggested something, it is explainability.
- If a message covers both a concept AND a career question, choose
  career_mentor. The concept can be handled on a later turn.
  - If the message is vague or short (e.g. "explain it", "give me an example")
  and RECENT CONVERSATION is provided, use it to infer what "it" refers to.
- If it is still ambiguous even with that context, do not guess confidently —
  set confidence below 0.5 and pick your best guess anyway.

### YOUR OUTPUT
Respond with:
- agent: one of study_coach, career_mentor, recommendation_system, explainability
- intent: one of the canonical intents listed above
- confidence: match the closest case
    0.9 - 1.0  the message clearly and only fits one agent
    0.7 - 0.8  it fits one agent, with some wording that could suggest another
    0.5 - 0.6  it genuinely fits two agents and you applied the rule above
- rationale: one sentence naming what in the message decided it
"""
        if context_summary:
            prompt += f"\n### CONTEXT (Optional background):\n\"\"\"{context_summary[:500]}\"\"\"\n"
        if history:
            prompt += (
                "\n### RECENT CONVERSATION (for resolving follow-ups; the "
                "current message may only make sense in light of this):\n"
                + "\n".join(history[-4:]) + "\n"
            )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=IntentDecision,
                ),
            )

            # 1. Try SDK parsed object
            if response.parsed and isinstance(response.parsed, IntentDecision):
                return response.parsed

            # 2. Try parsing raw JSON text from response
            raw_text = response.text or ""
            clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.IGNORECASE)
            clean_text = re.sub(r"\s*```$", "", clean_text)
            if clean_text:
                data = json.loads(clean_text)
                return IntentDecision(**data)

        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            print(f"[IntentClassifier] Classification failed: {exc}. Defaulting to study_coach.")

               # Classification failed. Default to the coach with zero confidence, so
        # the turn still works and the failure is visible in the logs.
        return IntentDecision(
            agent=AgentType.STUDY_COACH,
            intent="explain_concept",
            confidence=0.0,
            rationale="Classification failed; defaulted to study_coach.",
        )

    