
"""

"""
from pydantic import BaseModel , ConfigDict , Field
from uuid import UUID , uuid4
from datetime import datetime

class Reflection(BaseModel ): ##TODO we need to make this child of memory class
    """
    """
    model_config = ConfigDict(extra = "forbid")

    reflection_id : UUID = Field(
        default_factory=uuid4,
        description="Globally unique identifier for this reflection."
    )


    Content : str = Field (
        ...,
        min_length=3,
        description="the content of this reflection"

    )
    memories: List[str] = Field ( ## TODO change it later to list[memory]
        ...,

        description="list of the memories used to inference"

    )


    created_at : datetime = Field(
        default_factory= datetime.now,
        description= "creation date of this reflection"
    )