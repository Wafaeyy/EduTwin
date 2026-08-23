"""
preference_updater.py

Updates learner preference beliefs using resolved evidence.

PreferenceUpdater is responsible only for modifying Preference
components of the StudentTwin.

It does not:

- resolve entities
- interpret memories
- retrieve candidates
- create memories
- store memories

Preference beliefs are updated using an Exponential Moving Average
toward the direction indicated by the resolved evidence.
"""

from datetime import datetime

from src.twin.enums import (
    EvidenceDirection,
    PREFERENCE_OPTION_ENUMS,
    TwinComponent,
)
from src.twin.preference import Preference
from src.twin.student import StudentTwin
from src.updater.base import ComponentUpdater
from src.updater.resolver import ResolvedEvidence


class PreferenceUpdater(ComponentUpdater):
    """
    Updates learner preference affinities.

    Only the explicitly affected preference option is modified.

    Positive evidence moves the affinity toward 1.0.
    Negative evidence moves the affinity toward 0.0.
    """

    component_name = TwinComponent.PREFERENCE.value

    def __init__(
        self,
        alpha: float = 0.2,
    ) -> None:

        if not 0.0 < alpha <= 1.0:
            raise ValueError(
                "alpha must be greater than 0 and less than or equal to 1."
            )

        self.alpha = alpha

    # =============================================================
    # Public API
    # =============================================================

    def update(
        self,
        student: StudentTwin,
        evidence: ResolvedEvidence,
    ) -> str:
        """
        Apply resolved evidence to a learner preference.

        Existing preferences are updated in place.

        New preferences are created using the preference dimension,
        context, and option provided by the resolver.
        """

        if evidence.component != TwinComponent.PREFERENCE:
            raise ValueError(
                "PreferenceUpdater received evidence for "
                f"{evidence.component.value}."
            )

        if evidence.option is None:
            raise ValueError(
                "Preference evidence requires an option."
            )

        if evidence.direction is None:
            raise ValueError(
                "Preference evidence requires a direction."
            )

        if evidence.strength is None:
            raise ValueError(
                "Preference evidence requires a strength."
            )

        # ---------------------------------------------------------
        # Existing Preference
        # ---------------------------------------------------------

        if evidence.status.value == "existing":

            if evidence.entity_id is None:
                raise ValueError(
                    "Existing preference evidence requires entity_id."
                )

            preference = student.preferences.get(
                evidence.entity_id
            )

            if preference is None:
                raise ValueError(
                    "Preference entity was resolved as existing "
                    "but could not be found in the StudentTwin."
                )

            self._update_affinity(
                preference=preference,
                option=evidence.option,
                direction=evidence.direction,
                strength=evidence.strength,
                resolution_confidence = evidence.resolution_confidence,
            )

            preference.last_updated = datetime.now()

            return (
                f"Updated preference '{preference.dimension.value}' "
                f"in context '{preference.context.value}': "
                f"'{evidence.option}' moved "
                f"{evidence.direction.value}."
            )

        # ---------------------------------------------------------
        # New Preference
        # ---------------------------------------------------------

        if evidence.status.value == "new":

            if evidence.dimension is None:
                raise ValueError(
                    "New preference evidence requires dimension."
                )

            if evidence.context is None:
                raise ValueError(
                    "New preference evidence requires context."
                )

            preference = self._create_preference(
                dimension=evidence.dimension,
                context=evidence.context,
                option=evidence.option,
                direction=evidence.direction,
                strength=evidence.strength,
                resolution_confidence=evidence.resolution_confidence
            )

            student.preferences[
                preference.preference_id
            ] = preference

            return (
                f"Created new preference "
                f"'{preference.dimension.value}' "
                f"in context '{preference.context.value}' "
                f"with evidence for '{evidence.option}'."
            )

        raise ValueError(
            "PreferenceUpdater can only process "
            "EXISTING or NEW evidence."
        )

    # =============================================================
    # Existing Preference
    # =============================================================

    def _update_affinity(
        self,
        preference: Preference,
        option: str,
        direction: EvidenceDirection,
        strength: float,
        resolution_confidence:float
    ) -> None:
        """
        Update one preference affinity using EMA.

        Positive evidence targets 1.0.
        Negative evidence targets 0.0.
        """

        valid_options = {
            item.value
            for item in PREFERENCE_OPTION_ENUMS[
                preference.dimension
            ]
        }

        if option not in valid_options:
            raise ValueError(
                f"Invalid option '{option}' for "
                f"dimension '{preference.dimension.value}'."
            )

        if option not in preference.affinities:
            raise ValueError(
                f"Option '{option}' does not exist in the "
                "preference affinity vector."
            )

        current_affinity = preference.affinities[
            option
        ]

        target = (
            1.0
            if direction == EvidenceDirection.POSITIVE
            else 0.0
        )

        effective_alpha = self.alpha * strength * resolution_confidence

        new_affinity = (
            current_affinity
            + effective_alpha
            * (target - current_affinity)
        )

        preference.affinities[
            option
        ] = max(
            0.0,
            min(1.0, new_affinity),
        )

    # =============================================================
    # New Preference
    # =============================================================

    def _create_preference(
        self,
        dimension,
        context,
        option: str,
        direction: EvidenceDirection,
        strength: float,
        resolution_confidence : float,
    ) -> Preference:
        """
        Create a new Preference from the first piece of evidence.

        The affected option receives an evidence-based initial
        affinity.

        Other options receive a neutral prior.
        """

        valid_options = [
            item.value
            for item in PREFERENCE_OPTION_ENUMS[
                dimension
            ]
        ]

        if option not in valid_options:
            raise ValueError(
                f"Invalid option '{option}' for "
                f"dimension '{dimension.value}'."
            )

        # Neutral prior for options for which we have no evidence.
        neutral_prior = 0.5

        target = (
            1.0
            if direction == EvidenceDirection.POSITIVE
            else 0.0
        )

        initial_affinity = (
            neutral_prior
            + strength 
            * resolution_confidence
            * (target - neutral_prior)
        )

        affinities = {
            item: neutral_prior
            for item in valid_options
        }

        affinities[option] = max(
            0.0,
            min(1.0, initial_affinity),
        )

        return Preference(
            dimension=dimension,
            context=context,
            affinities=affinities,
        )