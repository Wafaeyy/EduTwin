"""
schemas.py

Pydantic schemas and data contracts for the EduTwin Agent Layer.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AgentType(str, Enum):
    """Supported agents in EduTwin."""
    STUDY_COACH = "study_coach"
    CAREER_MENTOR = "career_mentor"
    RECOMMENDATION_SYSTEM = "recommendation_system"
    EXPLAINABILITY = "explainability"


class IntentDecision(BaseModel):
    """
    Structured response from Gemini when classifying user intent.
    """
    model_config = ConfigDict(extra="forbid")

    agent: AgentType = Field(
        description="The specialized agent best suited to handle the student query."
    )
    intent: str = Field(
        description="The specific canonical intent label (e.g., explain_concept, check_answer, give_practice, career_fit_question, goal_change, resource_recommendation)."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in this classification."
    )
    rationale: str = Field(
        description="Short 1-sentence reasoning for choosing this agent and intent."
    )


class CoachSignal(BaseModel):
    """
    Diagnostic signal emitted by the Study Coach for the Digital Twin.
    Defined in docs/coach_twin_interface.md.
    """
    model_config = ConfigDict(extra="ignore")

    concept: str = Field(description="Canonical concept key.")
    signal: str = Field(
        description="Signal type: gap_confirmed | misconception_detected | mastery_evidence | mastery_unstable | confusion_resolved | briefing_contradicted"
    )
    detail: str = Field(description="One-sentence description of the observation.")
    evidence: str = Field(description="Direct student quote or observation in this session.")
    confidence: float = Field(ge=0.0, le=1.0, description="Session-local confidence score.")


class MentorProposal(BaseModel):
    """
    Proposal emitted by the Career Mentor for long-term twin updates.
    """
    model_config = ConfigDict(extra="ignore")

    type: str = Field(description="goal_change_detected | milestone_completed")
    detail: str = Field(description="Description of the change or milestone.")
    evidence: str = Field(description="What the student said.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score.")


class AgentResult(BaseModel):
    """
    The unified result returned by the Agent Orchestrator.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    reply: str = Field(
        description="The clean student-facing message (stripped of XML tags)."
    )
    agent_name: AgentType = Field(
        description="Which agent produced this response."
    )
    intent: str = Field(
        description="The detected intent."
    )
    raw_output: str = Field(
        default="",
        description="The full raw LLM text response including any tags."
    )
    signals: list[CoachSignal] = Field(
        default_factory=list,
        description="Any diagnostic signals emitted for the Twin (from Study Coach)."
    )
    proposals: list[MentorProposal] = Field(
        default_factory=list,
        description="Any proposals emitted for the Twin (from Career Mentor)."
    )
    report: dict[str, Any] | None = Field(
        default=None,
        description="Structured report from Career Mentor if present."
    )
    recommendations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recommendations list if processed by the Recommendation System."
    )
