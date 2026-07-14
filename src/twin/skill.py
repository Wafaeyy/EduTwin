
"""

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

    skill_level: float = Field (
        ge= 0.0,
        le = 1.0,
        description= "Describes the \"canthe user do it?\"  aspect"
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