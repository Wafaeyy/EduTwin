"""
goals.py

Defines the educational goals of a learner.

A Goal represents a desired educational outcome that guides
personalization, recommendation, planning, and progress tracking.

This model intentionally stores only the current state of a goal.
Historical changes are handled by the Memory System.

Research Question:
Can explicit learner goals improve educational personalization
compared to a stateless AI assistant?

Author: EduTwin Research Team
"""

from datetime import date
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

from twin.enums import GoalPriority, GoalStatus

class Goal(BaseModel):
    """
    Represents a single educational goal.

    Goals drive personalization throughout the Digital Twin.
    They are consumed by the Study Coach, Career Mentor,
    Recommendation Engine, and Prediction Module.
    """

    model_config = ConfigDict(extra="forbid")

    goal_id: UUID = Field(
        default_factory=uuid4,
        description="Globally unique identifier for this goal."
    )

    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Short title describing the goal."
    )

    description: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Detailed explanation of the educational goal."
    )

    priority: GoalPriority = Field(
        default=GoalPriority.MEDIUM,
        description="Relative importance of the goal."
    )

    status: GoalStatus = Field(
        default=GoalStatus.PLANNED,
        description="Current lifecycle state of the goal."
    )

    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Completion percentage of the goal."
    )

    target_completion_date: date | None = Field(
        default=None,
        description="Desired completion date for the goal."
    )