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

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


from twin.enums import MemoryType

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

    memory_type: MemoryType = Field(
        description="Type of learner interaction."
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

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the memory occurred."
    )