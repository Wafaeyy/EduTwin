from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from twin.enums import EvidenceSource


class Evidence(BaseModel):
    """
    Represents a single piece of retrieved evidence.

    All retrievers return Evidence objects regardless of the
    underlying data source.
    """

    source: EvidenceSource = Field(
        description="The retriever that produced this evidence."
    )

    content: str = Field(
        min_length=1,
        description="Natural language representation of the retrieved information."
    )

    reference_id: UUID | str = Field(
        description="Identifier of the original object from which the evidence was produced."
    )

    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional source-specific metadata associated with the evidence."
    )