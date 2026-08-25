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
        self._client = client
        self._api_key = api_key

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def classify(self, query: str, context_summary: str | None = None) -> IntentDecision:
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

### USER MESSAGE:
\"\"\"{query}\"\"\"
"""
        if context_summary:
            prompt += f"\n### CONTEXT (Optional background):\n\"\"\"{context_summary[:500]}\"\"\"\n"

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

        except Exception as exc:
            print(f"[IntentClassifier] LLM classification warning: {exc}. Using heuristic classifier fallback.")

        # Heuristic fallback if LLM classification fails
        return self._heuristic_fallback(query)

    def _heuristic_fallback(self, query: str) -> IntentDecision:
        """
        Rule-based fallback intent classification when LLM call is unavailable.
        """
        q = query.lower()

        # Career Mentor signals
        career_keywords = [
            "want to be", "want to become", "become a", "career", "job",
            "role", "engineer", "analyst", "developer", "switch to",
            "goal", "future", "market", "industry", "roadmap"
        ]
        if any(kw in q for kw in career_keywords):
            if any(k in q for k in ["want to be", "become", "switch to", "interested in being"]):
                intent = "goal_change"
            elif any(k in q for k in ["skills", "fit", "need to know", "requirements"]):
                intent = "career_fit_question"
            else:
                intent = "progress_alignment_check"

            return IntentDecision(
                agent=AgentType.CAREER_MENTOR,
                intent=intent,
                confidence=0.8,
                rationale="Heuristic match for career planning and role guidance.",
            )

        # Explainability signals (Check before recommendation since users often ask 'Why did you recommend X?')
        explain_keywords = ["why did you", "why do you", "explain why", "why was", "how did you decide", "reason for recommendation", "why is this recommended"]
        if any(kw in q for kw in explain_keywords):
            return IntentDecision(
                agent=AgentType.EXPLAINABILITY,
                intent="explain_decision",
                confidence=0.8,
                rationale="Heuristic match for system transparency/explanation.",
            )

        # Recommendation signals
        rec_keywords = ["recommend", "course", "video", "tutorial", "book", "resource", "link", "material", "where to learn"]
        if any(kw in q for kw in rec_keywords):
            return IntentDecision(
                agent=AgentType.RECOMMENDATION_SYSTEM,
                intent="resource_recommendation",
                confidence=0.8,
                rationale="Heuristic match for external resource request.",
            )

        # Study Coach signals (Default)
        if any(kw in q for kw in ["practice", "exercise", "quiz", "problem", "test me"]):
            intent = "give_practice"
        elif any(kw in q for kw in ["check", "correct", "verify", "is this right", "my answer"]):
            intent = "check_answer"
        else:
            intent = "explain_concept"

        return IntentDecision(
            agent=AgentType.STUDY_COACH,
            intent=intent,
            confidence=0.6,
            rationale="Heuristic match for academic coaching.",
        )
