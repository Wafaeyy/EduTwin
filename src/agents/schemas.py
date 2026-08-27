"""
schemas.py

Pydantic schemas and data contracts for the EduTwin Agent Layer.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentType(str, Enum):
    """Supported agents in EduTwin."""
    STUDY_COACH = "study_coach"
    CAREER_MENTOR = "career_mentor"
    RECOMMENDATION_SYSTEM = "recommendation_system"
    EXPLAINABILITY = "explainability"
    ##the next two classes added in order to be enum not string while pydantic model checks
class SignalType(str, Enum):
    """The six diagnostic signals the Study Coach may emit."""
    GAP_CONFIRMED = "gap_confirmed"
    MISCONCEPTION_DETECTED = "misconception_detected"
    MASTERY_EVIDENCE = "mastery_evidence"
    MASTERY_UNSTABLE = "mastery_unstable"
    CONFUSION_RESOLVED = "confusion_resolved"
    BRIEFING_CONTRADICTED = "briefing_contradicted"


class ProposalType(str, Enum):
    """The two proposals the Career Mentor may emit."""
    GOAL_CHANGE_DETECTED = "goal_change_detected"
    MILESTONE_COMPLETED = "milestone_completed"

class IntentDecision(BaseModel):
    """
    Structured response from Gemini when classifying user intent.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    agent: AgentType = Field(
        default=AgentType.STUDY_COACH,
        ##this description the model reads it as extra instructions
        description="The specialized agent best suited to handle the student query: study_coach, career_mentor, recommendation_system, or explainability."
    )
    intent: str = Field(
        default="explain_concept",
        description="The specific canonical intent label (e.g., explain_concept, check_answer, give_practice, career_fit_question, goal_change, progress_alignment_check, resource_recommendation, explain_decision)."
    )
    confidence: float = Field(
        default=0.0, ##edited
        ge=0.0,
        le=1.0,
        description="Confidence in this classification."
    )
    rationale: str = Field(
        default="",
        description="Short 1-sentence reasoning for choosing this agent and intent."
    )

    @field_validator("agent", mode="before")
    @classmethod
    def normalize_agent(cls, v: Any) -> AgentType:
        if isinstance(v, AgentType):
            return v
        ##edits from here
        if isinstance(v, str):
            clean = v.strip().lower().replace(" ", "_").replace("-", "_")

            # Exact match first — a valid value must never fall through to the
            # fuzzy checks below, where "study_coach_career_prep" would match
            # "career" and route to the wrong agent.
            for item in AgentType:
                if item.value == clean or item.name.lower() == clean:
                    return item

            # Fuzzy fallback for near-misses from the model.
            if "coach" in clean or "tutor" in clean or "study" in clean:
                return AgentType.STUDY_COACH
            if "career" in clean or "mentor" in clean:
                return AgentType.CAREER_MENTOR
            if "recommend" in clean or "resource" in clean:
                return AgentType.RECOMMENDATION_SYSTEM
            if "explain" in clean or "transparency" in clean:
                return AgentType.EXPLAINABILITY

        return AgentType.STUDY_COACH
        

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> float:
        if v is None:
            return 0.0 #edited
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.0 ##edited


class CoachSignal(BaseModel):
    """
    Diagnostic signal emitted by the Study Coach for the Digital Twin.
    Defined in docs/coach_twin_interface.md.
    """
    model_config = ConfigDict(extra="ignore")

    concept: str = Field(description="Canonical concept key.")
    ##changed the signal form str to enum class SignalType
    signal: SignalType = Field(
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
##changed type from str to the class (enums)
    type: ProposalType = Field(description="goal_change_detected | milestone_completed")
    detail: str = Field(description="Description of the change or milestone.")
    evidence: str = Field(description="What the student said.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score.")
## the following two classes added for the report of the career mentor
class GapEntry(BaseModel):
    """One ranked skill gap in the Mentor's report."""
    model_config = ConfigDict(extra="ignore")

    skill: str
    gap: float
    priority: int
    reason: str = ""


class MentorReport(BaseModel):
    """The Career Mentor's structured report.

    Typed rather than a bare dict so a malformed report fails HERE, at the
    parser, instead of downstream in whatever consumes gaps_ranked.
    """
    model_config = ConfigDict(extra="ignore")

    target_role: str
    required_profile: dict[str, float] = Field(default_factory=dict)
    current_profile: dict[str, float] = Field(default_factory=dict)
    gaps_ranked: list[GapEntry] = Field(default_factory=list)
    direction: str = ""
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
    )##change the report type from a dict to the class we built
    report: MentorReport | None = Field(
        default=None,
        description="Structured report from Career Mentor if present."
    
    )
    recommendations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recommendations list if processed by the Recommendation System."
    )
