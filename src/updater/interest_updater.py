"""
interest_updater.py

Updates learner Interest beliefs using resolved evidence.

An Interest represents the Digital Twin's current belief about
how strongly the learner is attracted to a particular topic.

Update strategy:

    Evidence-weighted Exponential Moving Average (EMA)

Positive evidence:

    A_new = A_old + alpha * strength * resolution_confidence
            * (1 - A_old)

Negative evidence:

    A_new = A_old - alpha * strength * resolution_confidence
            * A_old

Where:

    A = interest affinity

The updater directly modifies StudentTwin.

It does not perform:

- Memory creation
- Memory storage
- Entity resolution
- Retrieval
"""

from datetime import datetime

from src.twin.enums import (
    EvidenceDirection,
    ResolutionStatus,
    TwinComponent,
)
from src.twin.interest import Interest
from src.twin.student import StudentTwin

from src.updater.base import ComponentUpdater
from src.updater.resolver import ResolvedEvidence


class InterestUpdater(ComponentUpdater):
    """
    Updates Interest entities inside a StudentTwin.

    Existing interests are updated using an evidence-weighted EMA.

    New interests are initialized from the first piece of evidence
    with deliberately low confidence because one observation is not
    sufficient to establish a strong long-term belief.
    """

    component_name = TwinComponent.INTEREST.value

    def __init__(
        self,
        alpha: float = 0.25,
        beta: float = 0.20,
        initial_confidence: float = 0.10,
    ) -> None:

        if not 0.0 < alpha <= 1.0:
            raise ValueError(
                "alpha must be greater than 0 and at most 1."
            )

        if not 0.0 < beta <= 1.0:
            raise ValueError(
                "beta must be greater than 0 and at most 1."
            )

        if not 0.0 <= initial_confidence <= 1.0:
            raise ValueError(
                "initial_confidence must be between 0 and 1."
            )

        self.alpha = alpha
        self.beta = beta
        self.initial_confidence = initial_confidence

    # =============================================================
    # Public API
    # =============================================================

    def update(
        self,
        student: StudentTwin,
        evidence: ResolvedEvidence,
    ) -> str:
        """
        Apply resolved evidence to an Interest.

        EXISTING evidence updates an existing Interest.

        NEW evidence creates a new Interest.

        SKIP evidence is ignored.
        """

        if evidence.component != TwinComponent.INTEREST:
            raise ValueError(
                "InterestUpdater received evidence for "
                f"{evidence.component.value}."
            )

        if evidence.status == ResolutionStatus.SKIP:
            return ""

        if evidence.strength is None:
            raise ValueError(
                "Interest evidence requires strength."
            )

        if evidence.direction is None:
            raise ValueError(
                "Interest evidence requires direction."
            )

        if evidence.status == ResolutionStatus.EXISTING:
            return self._update_existing_interest(
                student=student,
                evidence=evidence,
            )

        if evidence.status == ResolutionStatus.NEW:
            return self._create_new_interest(
                student=student,
                evidence=evidence,
            )

        raise ValueError(
            f"Unsupported resolution status: "
            f"{evidence.status}"
        )

    # =============================================================
    # Existing Interest
    # =============================================================

    def _update_existing_interest(
        self,
        student: StudentTwin,
        evidence: ResolvedEvidence,
    ) -> str:
        """
        Apply EMA evidence update to an existing Interest.
        """

        if evidence.entity_id is None:
            raise ValueError(
                "EXISTING interest evidence requires entity_id."
            )

        interest = student.interests.get(
            evidence.entity_id
        )

        if interest is None:
            raise ValueError(
                "Interest referenced by ResolvedEvidence "
                "does not exist in the StudentTwin."
            )

        if evidence.strength is None:
            raise ValueError(
                "Interest evidence requires strength."
            )

        if evidence.resolution_confidence is None:
            raise ValueError(
                "Interest evidence requires resolution confidence."
            )

        old_affinity = interest.affinity
        old_confidence = interest.confidence

        # Resolution confidence determines how much we trust
        # the evidence as belonging to this particular interest.
        effective_weight = (
            self.alpha
            * evidence.strength
            * evidence.resolution_confidence
        )

        # ---------------------------------------------------------
        # Update affinity
        # ---------------------------------------------------------

        if evidence.direction == EvidenceDirection.POSITIVE:

            new_affinity = (
                old_affinity
                + effective_weight * (1.0 - old_affinity)
            )

        elif evidence.direction == EvidenceDirection.NEGATIVE:

            new_affinity = (
                old_affinity
                - effective_weight * old_affinity
            )

        else:
            raise ValueError(
                f"Unsupported evidence direction: "
                f"{evidence.direction}"
            )

        # ---------------------------------------------------------
        # Update confidence
        # ---------------------------------------------------------

        new_confidence = self._update_confidence(
            old_affinity=old_affinity,
            old_confidence=old_confidence,
            strength=evidence.strength,
            direction=evidence.direction,
        )

        interest.affinity = new_affinity
        interest.confidence = new_confidence
        interest.last_updated = datetime.now()

        return (
            f"Updated interest '{interest.topic}': "
            f"affinity {old_affinity:.3f} → "
            f"{new_affinity:.3f}, "
            f"confidence {old_confidence:.3f} → "
            f"{new_confidence:.3f}."
        )

    # =============================================================
    # New Interest
    # =============================================================

    def _create_new_interest(
        self,
        student: StudentTwin,
        evidence: ResolvedEvidence,
    ) -> str:
        """
        Create a new Interest from NEW evidence.

        The entity name comes from the resolver.

        Initial confidence is deliberately low because the
        Digital Twin has only one observation.
        """

        if evidence.entity_name is None:
            raise ValueError(
                "NEW interest evidence requires entity_name."
            )

        if evidence.strength is None:
            raise ValueError(
                "Interest evidence requires strength."
            )

        if evidence.direction == EvidenceDirection.POSITIVE:

            initial_affinity = evidence.strength

        elif evidence.direction == EvidenceDirection.NEGATIVE:

            initial_affinity = 1.0 - evidence.strength

        else:
            raise ValueError(
                f"Unsupported evidence direction: "
                f"{evidence.direction}"
            )

        interest = Interest(
            topic=evidence.entity_name,
            affinity=initial_affinity,
            confidence=self.initial_confidence,
        )

        student.interests[interest.interest_id] = interest

        return (
            f"Created interest '{interest.topic}': "
            f"affinity {interest.affinity:.3f}, "
            f"confidence {interest.confidence:.3f}."
        )

    # =============================================================
    # Confidence
    # =============================================================

    def _update_confidence(
        self,
        old_affinity: float,
        old_confidence: float,
        strength: float,
        direction: EvidenceDirection,
    ) -> float:
        """
        Update confidence based on whether the new evidence
        reinforces or contradicts the existing affinity belief.

        Resolution confidence is intentionally NOT used here.

        Reinforcing evidence increases confidence.

        Contradictory evidence decreases confidence.
        """

        if direction == EvidenceDirection.POSITIVE:

            reinforcing_strength = old_affinity

            contradictory_strength = 1.0 - old_affinity

        elif direction == EvidenceDirection.NEGATIVE:

            reinforcing_strength = 1.0 - old_affinity

            contradictory_strength = old_affinity

        else:
            raise ValueError(
                f"Unsupported evidence direction: "
                f"{direction}"
            )

        # The evidence is more reinforcing when it agrees with
        # the previous belief and more contradictory when it
        # disagrees with it.
        confidence_delta = (
            self.beta
            * strength
            * (reinforcing_strength - contradictory_strength)
        )

        new_confidence = old_confidence + confidence_delta

        return max(
            0.0,
            min(1.0, new_confidence),
        )