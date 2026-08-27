"""
orchestrator.py

Main agent routing and orchestration engine for EduTwin.
Coordinates intent classification, context building, agent execution,
and output parsing (including Twin signals and proposals).
"""

import json
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from src.agents.intent_classifier import IntentClassifier
from src.agents.parsers import parse_coach_output, parse_mentor_output
from src.agents.schemas import AgentResult, AgentType, IntentDecision
from src.twin.student import StudentTwin


# Default reference profiles for career mentor
DEFAULT_ROLE_PROFILES: dict[str, dict[str, Any]] = {
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


class AgentOrchestrator:
    """
    Coordinates intent classification, dispatches requests to the appropriate
    agent (Study Coach, Career Mentor, Recommender, Explainer), and extracts
    both student-facing text and structured Twin signals.
    """

    def __init__(
        self,
        model: str = "gemini-3.6-flash",
        client: genai.Client | None = None,
        api_key: str | None = None,
        role_profiles: dict[str, dict[str, Any]] | None = None,
    ):
        self.model = model
        self._client = client
        self._api_key = api_key
        self.classifier = IntentClassifier(model=model, client=client, api_key=api_key)
        self.role_profiles = role_profiles or DEFAULT_ROLE_PROFILES
        self.history: list[str] = [] 

        # Load system prompts
        prompts_dir = Path(__file__).parent / "prompts"
        self.coach_prompt = self._load_prompt(prompts_dir / "coach_system_v3.txt")
        self.mentor_prompt = self._load_prompt(prompts_dir / "mentor_system_v1.txt")
        self.explain_prompt = self._load_prompt(prompts_dir / "explain_v1.txt")

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    @staticmethod
    def _load_prompt(path: Path) -> str:
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def process(
        self,
        query: str,
        brief: str,
        history: list[str] | None = None,
        twin: StudentTwin | None = None,
        role: str | None = None,
        forced_intent: IntentDecision | None = None,
    ) -> AgentResult:
        """
        Executes the end-to-end agent workflow:
        1. Classifies intent and identifies target agent.
        2. Formats agent-specific prompt tags (including history, briefing, role profile).
        3. Calls Gemini with the agent's system prompt.
        4. Parses output into clean student-facing reply and structured signals.

        Args:
            query: The student's current message.
            brief: The context/briefing built by ContextBuilder.
            history: Optional multi-turn conversation history.
            twin: Optional StudentTwin object.
            role: Optional target role key (for Career Mentor).
            forced_intent: Optional pre-determined IntentDecision (bypasses classifier).

        Returns:
            AgentResult containing clean reply, signals, proposals, and metadata.
        """
                # Use the orchestrator's own running history unless the caller
        # explicitly passed one in. Capped at the last 3 exchanges (6 lines)
        # so old turns from unrelated topics don't pollute the current one.
        if history is None:
            history = self.history[-6:]
        # Step 1: Detect intent and choose agent
            intent_decision = forced_intent or self.classifier.classify(
            query=query, context_summary=brief, history=history
        )

        target_agent = intent_decision.agent
        intent = intent_decision.intent

        # Normalize target_agent if it's a string
        if isinstance(target_agent, str):
            clean = target_agent.strip().lower().replace(" ", "_").replace("-", "_")
            if "career" in clean or "mentor" in clean or "job" in clean:
                target_agent = AgentType.CAREER_MENTOR
            elif "coach" in clean or "tutor" in clean or "study" in clean:
                target_agent = AgentType.STUDY_COACH
            elif "recommend" in clean or "resource" in clean:
                target_agent = AgentType.RECOMMENDATION_SYSTEM
            elif "explain" in clean:
                target_agent = AgentType.EXPLAINABILITY
            else:
                for agent_enum in AgentType:
                    if agent_enum.value == clean or agent_enum.name.lower() == clean:
                        target_agent = agent_enum
                        break

        print(f"[Orchestrator] Routed query to: {target_agent.value} (intent: {intent})")

        # Step 2 & 3: Route and execute the appropriate agent
        if target_agent == AgentType.CAREER_MENTOR:
            # Determine role from argument, query text, twin goals, or default
            target_role = role
            if not target_role:
                q_lower = query.lower()
                for known_role in self.role_profiles.keys():
                    role_words = known_role.replace("_", " ").split()
                    if all(w in q_lower for w in role_words) or known_role in q_lower:
                        target_role = known_role
                        break
                    # Check partial matches like "machine learning" or "cybersecurity"
                    if any(part in q_lower for part in known_role.split("_") if len(part) > 4):
                        target_role = known_role
                        break
            if not target_role and twin and hasattr(twin, "goals") and twin.goals:
                first_goal = next(iter(twin.goals.values()), None)
                if first_goal and hasattr(first_goal, "title"):
                    target_role = first_goal.title.lower().replace(" ", "_")
            if not target_role:
                target_role = "machine_learning_engineer"

            result = self._run_mentor(query, intent, brief, history, target_role)
        elif target_agent == AgentType.RECOMMENDATION_SYSTEM:
            result = self._run_recommender(query, intent, brief, twin)
        elif target_agent == AgentType.EXPLAINABILITY:
            result = self._run_explainer(query, intent, brief, history)
        elif target_agent == AgentType.STUDY_COACH:
            result = self._run_coach(query, intent, brief, history)
        else:
            result = self._run_coach(query, intent, brief, history)

        # Record this turn AFTER the agent has answered, so the next call's
        # history includes it.
        self.history.append(f"Student: {query}")
        self.history.append(f"Assistant: {result.reply}")

        return result

    def _run_coach(
        self,
        query: str,
        intent: str,
        brief: str,
        history: list[str] | None = None,
    ) -> AgentResult:
        """Runs the Study Coach agent."""
        history_block = ""
        if history:
            history_block = (
                "<conversation_so_far>\n"
                + "\n".join(history)
                + "\n</conversation_so_far>\n\n"
            )

        user_block = f"""{history_block}<student_message>
{query}
</student_message>

<intent>
{intent}
</intent>

<briefing>
{brief}
</briefing>"""

        resp = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.coach_prompt
            ),
            contents=user_block,
        )
        raw_text = resp.text or ""
        clean_reply, signals = parse_coach_output(raw_text)

        return AgentResult(
            reply=clean_reply,
            agent_name=AgentType.STUDY_COACH,
            intent=intent,
            raw_output=raw_text,
            signals=signals,
        )

    def _run_mentor(
        self,
        query: str,
        intent: str,
        brief: str,
        history: list[str] | None = None,
        role: str = "machine_learning_engineer",
    ) -> AgentResult:
        """Runs the Career Mentor agent."""
        history_block = ""
        if history:
            history_block = (
                "<conversation_so_far>\n"
                + "\n".join(history)
                + "\n</conversation_so_far>\n\n"
            )

        role_profile_text = self._build_role_profile(role)

        user_block = f"""{history_block}<student_message>
{query}
</student_message>

<intent>
{intent}
</intent>

<briefing>
{brief}
</briefing>

<role_profile>
{role_profile_text}
</role_profile>"""

        resp = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.mentor_prompt
            ),
            contents=user_block,
        )
        raw_text = resp.text or ""
        clean_reply, report, proposals = parse_mentor_output(raw_text)

        return AgentResult(
            reply=clean_reply,
            agent_name=AgentType.CAREER_MENTOR,
            intent=intent,
            raw_output=raw_text,
            report=report,
            proposals=proposals,
        )

    def _run_recommender(
        self,
        query: str,
        intent: str,
        brief: str,
        twin: StudentTwin | None,
    ) -> AgentResult:
        """Runs the recommendation agent."""
        from src.agents.recommendation_system.orchestrator_interface import recommend_text

        reply_text = recommend_text(brief,query)

        return AgentResult(
            reply=reply_text,
            agent_name=AgentType.RECOMMENDATION_SYSTEM,
            intent=intent,
            raw_output=reply_text,
        )

    def _run_explainer(
        self,
        query: str,
        intent: str,
        brief: str,
        history: list[str] | None = None,
    ) -> AgentResult:
        """Runs the Explainability agent."""
        prompt = f"""
<student_message>
{query}
</student_message>

<intent>
{intent}
</intent>

<briefing>
{brief}
</briefing>
"""
        resp = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.explain_prompt
            ),
            contents=prompt,
        )
        reply_text = resp.text or ""
        return AgentResult(
            reply=reply_text,
            agent_name=AgentType.EXPLAINABILITY,
            intent=intent,
            raw_output=reply_text,
        )

    def _build_role_profile(self, role: str) -> str:
        """Builds role profile text representation."""
        entry = self.role_profiles.get(role)
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


def route_and_execute_agent(
    query: str,
    brief: str,
    history: list[str] | None = None,
    twin: StudentTwin | None = None,
    orchestrator: AgentOrchestrator | None = None,
) -> AgentResult:
    """
    Convenience function for routing and executing the appropriate agent.

    Usage in main.py:
        agent_result = route_and_execute_agent(query=query, brief=brief, twin=twin)
        agent_answer = agent_result.reply
    """
    orch = orchestrator or AgentOrchestrator()
    return orch.process(query=query, brief=brief, history=history, twin=twin)
