from typing import Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.memory.memory import MemoryType


class TimeRange(BaseModel):
    """
    Represents an optional time constraint for retrieval.
    """

    start: datetime = Field(
        description="Start of the retrieval time window."
    )

    end: datetime = Field(
        description="End of the retrieval time window."
    )


class RetrievalRequest(BaseModel):
    """
    Represents a retrieval request for the EduTwin retrieval layer.

    A RetrievalRequest specifies:
    - Which student's data should be searched.
    - What information is being requested.
    - Which knowledge sources should participate.
    - Optional constraints on the retrieval process.
    """

    student_id: UUID = Field(
        description="Unique identifier of the student."
    )

    query: str = Field(
        min_length=1,
        description="Natural language query describing the information need."
    )

    top_k: int = Field(
        default=10,
        ge=1,
        description="Maximum number of evidence items each retriever should return."
    )

    max_context_tokens: int = Field(
        default=4000,
        ge=1,
        description="Maximum token budget for the final retrieval context."
    )

    include_memory: bool = Field(
        default=True,
        description="Whether the MemoryRetriever should be used."
    )

    include_twin: bool = Field(
        default=True,
        description="Whether the TwinRetriever should be used."
    )

    include_graph: bool = Field(
        default=True,
        description="Whether the GraphRetriever should be used."
    )

    memory_types: list[MemoryType] | None = Field(
        default=None,
        description="Optional memory types to restrict memory retrieval."
    )

    time_range: TimeRange | None = Field(
        default=None,
        description="Optional time range limiting retrieved memories."
    )
    
    metadata_filters: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata constraints applied during retrieval."
    )