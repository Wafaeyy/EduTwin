"""
intent_classifier.py

Classifies user messages to detect intent and route to the appropriate AI agent.
"""

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
   - "goal_change": Student expresses interest in changing their primary career goal or learning direction.

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
            return response.parsed
        except Exception as exc:
            # Safe fallback if network error, missing key, or transient failure occurs
            return IntentDecision(
                agent=AgentType.STUDY_COACH,
                intent="explain_concept",
                confidence=0.5,
                rationale=f"Fallback due to classification exception: {exc}",
            )
