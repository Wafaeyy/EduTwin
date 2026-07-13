"""
profile.py

Defines the static identity information of a learner.

This module intentionally excludes dynamic educational data such as
skills, knowledge, goals, preferences, and memories. Those concepts
are represented by dedicated models elsewhere in the Digital Twin.

Research Question:
Can learner identity be represented independently from evolving
educational attributes?

Author: EduTwin Research Team
"""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict
from twin import enums  


class Profile(BaseModel):
    """
    Represents the static identity of a learner.

    This model stores demographic and academic identity information
    that changes infrequently throughout the learner's journey.
    """
    model_config = ConfigDict(extra= "forbid")

    student_id: UUID = Field(
        default_factory=uuid4,
        description="Globally unique identifier for the learner."
    )

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full legal or preferred name of the learner."
    )

    university: str = Field(
        ...,
        description="University or educational institution."
    )

    fied_of_study: str = Field(
        ...,
        description="Primary field of study."
    )

    education_stage: enums.EducationStage

    current_year: int | None = Field(
        default= None,
        ge=1,
        le=7,
        description="Current academic year (1-7)."
        )