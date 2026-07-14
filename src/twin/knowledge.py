
"""
knowledge.py

Defines the learner's knowledge state within the EduTwin Digital Twin.

A Knowledge record represents the Digital Twin's current belief
about the learner's mastery of a specific educational topic.

This model intentionally stores only the current belief state.
Historical changes are managed by the Memory System.

Research Question:
Can probabilistic knowledge estimates improve educational
personalization compared to deterministic learner models?

"""
from pydantic import BaseModel , ConfigDict , Field
from uuid import UUID , uuid4
from datetime import datetime

class Knowledge(BaseModel):
    """
    Represents the learner's current knowledge state
    for a specific educational topic.

    Knowledge estimates are consumed by the Recommendation Engine,
    Study Coach, Assessment Module, and Prediction Module to
    personalize the learner's educational experience.
    """
    model_config = ConfigDict(extra = "forbid")

    knowledge_id : UUID = Field(
        default_factory=uuid4,
        description="Globally unique identifier for this knowledge record."
    )


    topic : str = Field (
        ...,
        min_length=3,
        max_length= 100 ,
        description="Topic name."

    )

    mastery: float = Field (
        ge= 0.0,
        le = 1.0,
        description= "Estimated mastery level assigned by the Digital Twin."
    )

    confidence : float = Field (
        ge =0.0,
        le = 1.0,
        description="Confidence of the Digital Twin in the mastery estimate."
    )

    last_updated : datetime = Field(
        default_factory= datetime.now,
        description= "last update date of this knowledge"
    )