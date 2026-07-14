"""
preference.py

Defines contextual learner preferences for the EduTwin Digital Twin.

Unlike traditional systems that store deterministic preferences,
EduTwin models preferences as contextual affinity beliefs.

The Digital Twin stores only the current belief state.

Preference updates are performed exclusively by the Twin Updater.

Research Question:
Can contextual affinity beliefs better represent learner preferences
than deterministic preference values?

Author: EduTwin Research Team
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class PreferenceOption(BaseModel):
    """
    Represents one possible option within a preference dimension.

    Example:

    value = "Detailed"

    affinity = 0.91
    """

    model_config = ConfigDict(extra="forbid")

    value: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Possible value for this preference."
    )

    affinity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Current affinity score assigned by the Digital Twin."
    )   


class Preference(BaseModel):
    """
    Represents a contextual preference belief.

    Example

    Dimension:
        Explanation Depth

    Context:
        Programming

    Affinities:
        Short      0.18
        Medium     0.61
        Detailed   0.92
    """

    model_config = ConfigDict(extra="forbid")

    preference_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this preference."
    )

    dimension: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Preference dimension (e.g. Explanation Depth)."
    )

    context: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Context in which this preference applies."
    )

    options: list[PreferenceOption] = Field(
        ...,
        min_items=1,
        description="Affinity scores for every available option."
    )

    last_updated: datetime = Field(
        default_factory=datetime. now,
        description="Timestamp of the latest belief update."
    )