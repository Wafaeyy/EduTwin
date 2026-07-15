"""
preferences.py

Represents contextual learner preferences using affinity belief vectors.

Each preference consists of:

- Dimension
- Context
- Affinity Vector

Affinity values range from 0.0 to 1.0 and represent the Digital Twin's
current belief about how strongly the learner prefers each option.

The Twin stores only the current belief state.

Historical evidence is stored by the Memory System.

Only the Twin Updater may modify these beliefs.
"""

from uuid import UUID, uuid4
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from twin.enums import (
    PreferenceDimension,
    PREFERENCE_OPTION_ENUMS,
    LearningContext
)


class Preference(BaseModel):

    model_config = ConfigDict(extra="forbid")

    preference_id: UUID = Field(
        default_factory=uuid4
    )

    dimension: PreferenceDimension = Field(
        description="Preference dimension."
    )

    context: LearningContext = Field(
        description="Context in which the preference applies."
    )

    affinities: dict[str, float] = Field(
        description="Affinity score for each valid option."
    )

    last_updated: datetime = Field(
        default_factory=datetime.now
    )

    @field_validator("affinities")
    @classmethod
    def validate_affinities(cls, affinities, info):

        dimension = info.data.get("dimension")

        if dimension is None:
            return affinities

        enum_cls = PREFERENCE_OPTION_ENUMS[dimension]

        valid_options = {e.value for e in enum_cls}

        invalid = set(affinities.keys()) - valid_options

        if invalid:
            raise ValueError(
                f"Invalid options {invalid} for dimension {dimension.value}"
            )

        for score in affinities.values():
            if not (0.0 <= score <= 1.0):
                raise ValueError(
                    "Affinity scores must be between 0 and 1."
                )

        return affinities