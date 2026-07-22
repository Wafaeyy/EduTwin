"""
student.py

Defines the Student Digital Twin.

The StudentTwin represents the learner's current state by aggregating
all learner-related models into a single object.

It contains no business logic.

Only the Twin Updater is responsible for modifying the Twin.
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from twin.profile import Profile
from twin.goal import Goal
from twin.preference import Preference
from twin.knowledge import Knowledge
from twin.skill import Skill
from twin.interest import Interest


class StudentTwin(BaseModel):
    """
    Aggregate root of the learner's Digital Twin.

    This model groups together every aspect of the learner's current
    state. It is the primary object consumed by AI agents throughout
    the EduTwin architecture.

    Historical interactions are stored separately by the Memory System.
    """

    model_config = ConfigDict(extra="forbid")

    twin_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier of this Digital Twin."
    )

    profile: Profile = Field(
        description="Static learner identity."
    )

    goals: dict[UUID, Goal] = Field(
        default_factory=dict,
        description="Current learner goals."
    )

    preferences: dict[UUID, Preference] = Field(
        default_factory=dict,
        description="Current learner preferences."
    )

    knowledge: dict[UUID, Knowledge] = Field(
        default_factory=dict,
        description="Current learner knowledge estimates."
    )

    skills: dict[UUID, Skill] = Field(
        default_factory=dict,
        description="Current learner skill estimates."
    )

    interests: dict[UUID, Interest] = Field(
        default_factory=dict,
        description="Current learner interests."
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the Twin was created."
    )

    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of the latest Twin update."
    )