"""
interest.py

Defines the learner's interests within the EduTwin Digital Twin.

An Interest represents the Digital Twin's current belief about how
strongly the learner is attracted to a particular educational domain
or subject.

Interests model learner motivation rather than competence.

Historical evidence is managed by the Memory System.

Research Question:
Can modeling learner interests independently from knowledge, skills,
and goals improve long-term educational personalization?
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Interest(BaseModel):
    """
    Represents the learner's current interest in an educational topic.

    Interest estimates describe motivation and curiosity rather than
    knowledge or practical ability.

    The Recommendation Engine may use interests to prioritize learning
    resources that are both educationally useful and intrinsically
    motivating.
    """

    model_config = ConfigDict(extra="forbid")

    interest_id: UUID = Field(
        default_factory=uuid4,
        description="Globally unique identifier for this interest record."
    )

    topic: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Educational topic or domain of interest."
    )

    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional description of the interest."
    )

    affinity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Estimated strength of the learner's interest "
            "in this topic."
        )
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence of the Digital Twin in the affinity estimate."
        )
    )

    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the latest Twin update."
    )