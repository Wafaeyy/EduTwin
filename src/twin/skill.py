
"""
skill.py

Defines the learner's practical skills within the EduTwin Digital Twin.

A Skill represents the Digital Twin's current belief about the learner's
ability to perform a specific task or activity.

This model intentionally stores only the current belief state.
Historical changes are managed by the Memory System.

Research Question:
Can separating practical skills from conceptual knowledge improve
educational personalization and learner modeling?
"""
from pydantic import BaseModel , ConfigDict , Field
from uuid import UUID , uuid4
from datetime import datetime

class Skill(BaseModel):
    """

    """
    model_config = ConfigDict(extra = "forbid")

    skill_id : UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this."
    )


    name : str = Field (
        ...,
        min_length=3,
        max_length= 100 ,
        description="Topic name."

    )

    description: str | None = Field(
    default=None,
    max_length=500,
    description="Optional description of the skill."
    )

    skill_level: float = Field (
        ge= 0.0,
        le = 1.0,
        description= "Describes the \"can the user do it?\"  aspect"
    )

    confidence : float = Field (
        ge =0.0,
        le = 1.0,
        description="Confidence of the Digital Twin in the skill_level estimate."
    )

    last_updated : datetime = Field(
        default_factory= datetime.now,
        description= "last update date of this knowledge"
    )
