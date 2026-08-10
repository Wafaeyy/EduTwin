"""
skill_updater.py

Updates learner Skill beliefs using resolved evidence.

Skill beliefs consist of:

- skill_level:
    Current estimate of the learner's ability.

- confidence:
    Confidence of the Digital Twin in that estimate.

Update strategy:

Evidence-weighted Exponential Moving Average (EMA)

Positive evidence:

    L_new = L_old + alpha * strength * confidence * (1 - L_old)

Negative evidence:

    L_new = L_old - alpha * strength * confidence * L_old

The update naturally remains within [0, 1] and produces
diminishing changes as the estimate approaches either boundary.

The updater directly modifies StudentTwin.
It does not perform retrieval, resolution, or memory storage.
"""

from datetime import datetime

from src.twin.enums import (
    EvidenceDirection,
    ResolutionStatus,
    TwinComponent,
)
from src.twin.skill import Skill
from src.twin.student import StudentTwin

from src.updater.base import ComponentUpdater
from src.updater.resolver import ResolvedEvidence


class SkillUpdater(ComponentUpdater):
    """
    Updates Skill entities inside a StudentTwin.

    Uses an evidence-weighted EMA update for existing skills
    and evidence-derived initialization for new skills.
    """

    component_name = TwinComponent.SKILL.value

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
        Apply resolved evidence to a Skill.

        EXISTING evidence updates an existing Skill.

        NEW evidence creates a new Skill.

        SKIP evidence is ignored.
        """

        if evidence.component != TwinComponent.SKILL:
            raise ValueError(
                "SkillUpdater received evidence for "
                f"{evidence.component.value}."
            )

        if evidence.status == ResolutionStatus.SKIP:
            return ""

        if evidence.strength is None:
            raise ValueError(
                "Skill evidence requires strength."
            )

        if evidence.direction is None:
            raise ValueError(
                "Skill evidence requires direction."
            )
            
        if evidence.resolution_confidence is None:
                    raise ValueError(
                        "NEW skill evidence requires resolution confidence."
                    )

        if evidence.status == ResolutionStatus.EXISTING:
            return self._update_existing_skill(
                student=student,
                evidence=evidence,
            )

        if evidence.status == ResolutionStatus.NEW:
            return self._create_new_skill(
                student=student,
                evidence=evidence,
            )

        raise ValueError(
            f"Unsupported resolution status: "
            f"{evidence.status}"
        )

    # =============================================================
    # Existing Skill
    # =============================================================

    def _update_existing_skill(
        self,
        student: StudentTwin,
        evidence: ResolvedEvidence,
    ) -> str:
        """
        Apply EMA evidence update to an existing Skill.
        """

        if evidence.entity_id is None:
            raise ValueError(
                "EXISTING skill evidence requires entity_id."
            )

        skill = student.skills.get(
            evidence.entity_id
        )

        if skill is None:
            raise ValueError(
                "Skill referenced by ResolvedEvidence "
                "does not exist in the StudentTwin."
            )

        old_level = skill.skill_level
        old_confidence = skill.confidence

        effective_weight = (
            self.alpha
            * evidence.strength
            * evidence.resolution_confidence
        )

        # ---------------------------------------------------------
        # Update skill level
        # ---------------------------------------------------------

        if evidence.direction == EvidenceDirection.POSITIVE:

            new_level = (
                old_level
                + effective_weight * (1.0 - old_level)
            )

        elif evidence.direction == EvidenceDirection.NEGATIVE:

            new_level = (
                old_level
                - effective_weight * old_level
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
            old_confidence=old_confidence,
            strength=evidence.strength,
            direction=evidence.direction,
        )

        skill.skill_level = new_level
        skill.confidence = new_confidence
        skill.last_updated = datetime.now()

        return (
            f"Updated skill '{skill.name}': "
            f"skill_level {old_level:.3f} → {new_level:.3f}, "
            f"confidence {old_confidence:.3f} → "
            f"{new_confidence:.3f}."
        )

    # =============================================================
    # New Skill
    # =============================================================

    def _create_new_skill(
        self,
        student: StudentTwin,
        evidence: ResolvedEvidence,
    ) -> str:
        """
        Create a new Skill from NEW evidence.

        The entity name comes from the resolver.
        """

        if evidence.entity_name is None:
            raise ValueError(
                "NEW skill evidence requires entity_name."
            )

        # ---------------------------------------------------------
        # Initial skill estimate
        # ---------------------------------------------------------

        if evidence.direction == EvidenceDirection.POSITIVE:

            initial_level = evidence.strength

        elif evidence.direction == EvidenceDirection.NEGATIVE:

            initial_level = 1.0 - evidence.strength

        else:
            raise ValueError(
                f"Unsupported evidence direction: "
                f"{evidence.direction}"
            )

        # ---------------------------------------------------------
        # Create Skill
        # ---------------------------------------------------------

        skill = Skill(
            name=evidence.entity_name,
            skill_level=initial_level,
            confidence= self.initial_confidence ,
        )

        student.skills[skill.skill_id] = skill

        return (
            f"Created skill '{skill.name}': "
            f"skill_level {skill.skill_level:.3f}, "
            f"confidence {skill.confidence:.3f}."
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