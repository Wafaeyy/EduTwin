"""
memory.py

Defines immutable memories stored by the EduTwin Memory System.

A Memory represents an observed learner interaction or event that may
later influence the Digital Twin.

Memories store evidence rather than learner beliefs.

Historical memories are never modified after creation.

Research Question:
Can separating immutable interaction memories from learner beliefs
improve explainability and long-term personalization?
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


from src.twin.enums import TwinComponent

class Memory(BaseModel):
    """
    Immutable evidence collected about the learner.

    Memories are stored permanently and later interpreted by the
    Twin Updater to update the learner's Digital Twin.
    """

    model_config = ConfigDict(extra="forbid")

    memory_id: UUID = Field(
        default_factory=uuid4,
        description="Globally unique identifier for this memory."
    )

    affected_components: list[TwinComponent] = Field(
        ...,
        default_factory= list,
        description=(
            "Twin components that may be affected by this memory."
        )
    )

    content: str = Field(
        ...,
        min_length=1,
        description="Human-readable description of the observed event."
    )

    importance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relative importance of this memory."
    )
    
    archived: bool = Field(
        default= False,
        description="bool value if memory is archived or no"
    )

    created_at: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc)
)