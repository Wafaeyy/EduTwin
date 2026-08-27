"""
resolver.py

Resolves newly created memories against the learner's StudentTwin.

Pipeline:

Memory
    ↓
Affected Twin Components
    ↓
TwinStore Candidate Retrieval
    ↓
LLM Candidate Resolution
    ↓
ResolvedEvidence
    ↓
TwinUpdater

The resolver does NOT modify the StudentTwin.

Responsibilities:

- Retrieve candidate Twin entities.
- Determine whether evidence refers to an existing entity.
- Identify when a new entity is needed.
- Determine evidence direction.
- Determine evidence strength.
- Provide resolution confidence.
- Resolve preference dimensions, contexts, and options.

The resolver never generates Twin entity UUIDs.
"""

from uuid import UUID

from google import genai
from pydantic import BaseModel, ConfigDict, Field

from src.memory.memory import Memory
from src.twin.enums import (
    EvidenceDirection,
    LearningContext,
    PREFERENCE_OPTION_ENUMS,
    PreferenceDimension,
    ResolutionStatus,
    TwinComponent,
)
from src.twin.interest import Interest
from src.twin.knowledge import Knowledge
from src.twin.preference import Preference
from src.twin.skill import Skill
from src.twin.student import StudentTwin
from src.twin.twin_store import TwinStore


TwinItem = Skill | Knowledge | Interest | Preference


# =====================================================================
# Resolver Models
# =====================================================================


class TwinCandidate(BaseModel):
    """
    A candidate Twin entity retrieved from the TwinStore.

    This is an intermediate representation used by the resolver.
    """

    model_config = ConfigDict(extra="forbid")

    component: TwinComponent

    entity_id: UUID

    name: str

    description: str | None = None

    similarity: float = Field(
        ge=0.0,
        le=1.0,
    )

    # Preference-specific information.
    preference_dimension: PreferenceDimension | None = None

    preference_context: LearningContext | None = None

    preference_options: list[str] | None = None


class ResolvedEvidence(BaseModel):
    """
    Evidence resolved from a Memory to a Twin component/entity.

    The resolver determines WHAT the evidence refers to and
    interprets the evidence direction and strength.

    The Twin Updater determines HOW the corresponding learner
    belief should be updated.
    """

    model_config = ConfigDict(extra="forbid")

    memory_id: UUID = Field(
        description="ID of the memory from which this evidence originated."
    )

    component: TwinComponent = Field(
        description="Twin component affected by the evidence."
    )

    status: ResolutionStatus = Field(
        description="Resolution outcome."
    )

    entity_id: UUID | None = Field(
        default=None,
        description=(
            "ID of the existing Twin entity when resolution "
            "status is EXISTING."
        ),
    )

    entity_name: str | None = Field(
        default=None,
        description=(
            "Name of the affected entity. Used for existing or "
            "new entities."
        ),
    )

    # Preference-specific information.
    dimension: PreferenceDimension | None = Field(
        default=None,
        description=(
            "Preference dimension affected by the evidence. "
            "Used only when component is PREFERENCE."
        ),
    )

    context: LearningContext | None = Field(
        default=None,
        description=(
            "Learning context in which the preference applies. "
            "Used only when component is PREFERENCE."
        ),
    )

    option: str | None = Field(
        default=None,
        description=(
            "Specific preference option affected by the evidence. "
            "Used only when component is PREFERENCE."
        ),
    )

    direction: EvidenceDirection | None = Field(
        default=None,
        description=(
            "Direction of the evidence. Positive reinforces the "
            "current belief, while negative weakens it."
        ),
    )

    strength: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Strength of the evidence itself, independent of "
            "resolution confidence."
        ),
    )

    resolution_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence that the memory was correctly resolved "
            "to the selected entity."
        ),
    )

    reason: str = Field(
        min_length=1,
        description="Explanation for the resolution decision.",
    )


class ResolutionDecision(BaseModel):
    """
    Structured Gemini output used by the resolver.

    Gemini chooses among candidates by index. It never generates
    or invents Twin entity UUIDs.
    """

    ##model_config = ConfigDict(extra="forbid")

    status: ResolutionStatus

    candidate_index: int | None = Field(
        default=None,
        description=(
            "Index of the selected candidate when status is EXISTING. "
            "Must be null otherwise."
        ),
    )

    entity_name: str | None = Field(
        default=None,
        description=(
            "Name of the entity when status is NEW. "
            "Must be null for EXISTING and SKIP."
        ),
    )

    # Preference-specific fields.
    dimension: PreferenceDimension | None = Field(
        default=None,
        description=(
            "Preference dimension when resolving a preference. "
            "Required for NEW preference evidence."
        ),
    )

    context: LearningContext | None = Field(
        default=None,
        description=(
            "Learning context when resolving a preference. "
            "Required for NEW preference evidence."
        ),
    )

    option: str | None = Field(
        default=None,
        description=(
            "Specific preference option affected by the evidence. "
            "Required when resolving a preference."
        ),
    )

    direction: EvidenceDirection | None = Field(
        default=None,
        description=(
            "Whether the evidence supports or contradicts "
            "the current belief."
        ),
    )

    strength: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Strength of the evidence.",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence that the resolution decision is correct."
        ),
    )

    reason: str = Field(
        min_length=1,
        description="Explanation for the resolution decision.",
    )


# =====================================================================
# Resolver
# =====================================================================


class TwinEntityResolver:
    """
    Resolves memory evidence to entities in a StudentTwin.

    The resolver never modifies the Twin.
    """

    def __init__(
        self,
        twin_store: TwinStore,
        top_k: int = 5,
    ) -> None:

        self.twin_store = twin_store
        self.top_k = top_k

        self.gemini = genai.Client()

    # =================================================================
    # Public API
    # =================================================================

    def resolve(
        self,
        student: StudentTwin,
        memory: Memory,
    ) -> list[ResolvedEvidence]:
        """
        Resolve a memory against all Twin components identified
        by the memory's affected_components field.
        """

        resolved: list[ResolvedEvidence] = []

        for component in memory.affected_components:

            # Goals are not currently searchable through TwinStore.
            # Their resolution mechanism will be implemented separately.
            if component == TwinComponent.GOAL:

                resolved.append(
                    ResolvedEvidence(
                        memory_id=memory.memory_id,
                        component=component,
                        status=ResolutionStatus.SKIP,
                        resolution_confidence=0.0,
                        reason=(
                            "Goal resolution is not implemented yet."
                        ),
                    )
                )

                continue

            candidates = self._retrieve_candidates(
                student=student,
                memory=memory,
                component=component,
            )

            evidence = self._resolve_candidates(
                memory=memory,
                component=component,
                candidates=candidates,
            )

            resolved.append(evidence)

        return resolved

    # =================================================================
    # Candidate Retrieval
    # =================================================================

    def _retrieve_candidates(
        self,
        student: StudentTwin,
        memory: Memory,
        component: TwinComponent,
    ) -> list[TwinCandidate]:
        """
        Retrieve semantic candidates for a specific Twin component.

        TwinStore searches all searchable Twin components, so the
        resolver retrieves a larger pool and filters it by component.
        """

        results = self.twin_store.search(
            twin_id=student.twin_id,
            query=memory.content,
            top_n=self.top_k * 4,
        )

        candidates: list[TwinCandidate] = []

        for item, similarity in results:

            if self._get_component(item) != component:
                continue

            candidate = self._candidate_from_item(
                item=item,
                similarity=similarity,
            )

            candidates.append(candidate)

            if len(candidates) >= self.top_k:
                break

        return candidates

    # =================================================================
    # Candidate Resolution
    # =================================================================

    def _resolve_candidates(
        self,
        memory: Memory,
        component: TwinComponent,
        candidates: list[TwinCandidate],
    ) -> ResolvedEvidence:
        """
        Determine whether the memory refers to an existing entity,
        a new entity, or should be skipped.

        Gemini performs semantic interpretation only.

        It never generates or receives Twin entity UUIDs.
        """

        candidate_text = self._format_candidates(
            candidates
        )

        preference_instructions = ""

        if component == TwinComponent.PREFERENCE:

            preference_instructions = f"""
PREFERENCE-SPECIFIC RULES:

This evidence concerns a learner preference.

For EXISTING preference candidates:

- Use the selected candidate's dimension and context.
- The option MUST be one of the candidate's valid options.
- Do not invent an option.
- Return the exact option string.

For NEW preference evidence:

- Determine the appropriate preference dimension.
- Determine the appropriate learning context.
- Select an option from the valid options of that dimension.
- Do not invent option names.

VALID PREFERENCE DIMENSIONS:

{self._format_preference_dimensions()}

VALID LEARNING CONTEXTS:

{self._format_learning_contexts()}

For the selected dimension, valid options are defined by the
EduTwin preference vocabulary.

The option must correspond to one of those valid options.
"""

        prompt = f"""
You are the Twin Entity Resolver of EduTwin.

Your task is to resolve one piece of learner evidence against
one specific component of the learner's Digital Twin.

MEMORY:
{memory.content}

TARGET TWIN COMPONENT:
{component.value}

EXISTING CANDIDATES:
{candidate_text}

Determine the relationship between the memory and this
Twin component.

Possible outcomes:

EXISTING:
The memory clearly refers to one specific existing candidate.

NEW:
The memory contains meaningful evidence about an entity belonging
to this component, but none of the existing candidates represent it.

SKIP:
The evidence is irrelevant to this component OR the evidence
is too ambiguous to safely associate with an entity.

Rules:

1. Do not select an existing candidate merely because it has
   the highest semantic similarity.

2. Semantic similarity is supporting evidence, not proof.

3. Select EXISTING only when the memory clearly refers to one
   specific candidate.

4. Select NEW only when the memory contains meaningful evidence
   about an entity that is not represented by the candidates.

5. Select SKIP when the evidence is irrelevant, ambiguous,
   or insufficiently specific.

6. If multiple candidates are plausible and the memory does not
   distinguish between them, select SKIP.

7. For EXISTING candidate_index must be provided.

8. For NEW you must provide entity_name.

9. Never generate or infer a UUID.

10. For EXISTING and NEW, determine the direction of the evidence:

    POSITIVE:
    The evidence supports or reinforces the current belief.

    NEGATIVE:
    The evidence contradicts or weakens the current belief.

11. strength represents how strongly the memory supports the
    direction of the evidence.

12. resolution confidence represents how confident you are that
    your resolution decision is correct.

13. Strength and resolution confidence are different concepts.

14. For SKIP, direction and strength must be null.

15. For EXISTING and NEW, direction and strength must be provided.

{preference_instructions}
"""

        response = self.gemini.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ResolutionDecision,
            },
        )

        decision = response.parsed

        return self._build_resolved_evidence(
            memory=memory,
            component=component,
            decision=decision,
            candidates=candidates,
        )

    # =================================================================
    # Result Construction
    # =================================================================

    @staticmethod
    def _build_resolved_evidence(
        memory: Memory,
        component: TwinComponent,
        decision: ResolutionDecision,
        candidates: list[TwinCandidate],
    ) -> ResolvedEvidence:
        """
        Convert the LLM decision into application-level
        ResolvedEvidence.

        UUIDs always come from actual Twin candidates.
        """

        # -------------------------------------------------------------
        # SKIP
        # -------------------------------------------------------------

        if decision.status == ResolutionStatus.SKIP:

            return ResolvedEvidence(
                memory_id=memory.memory_id,
                component=component,
                status=ResolutionStatus.SKIP,
                direction=None,
                strength=None,
                resolution_confidence=decision.confidence,
                reason=decision.reason,
            )

        # -------------------------------------------------------------
        # Preference validation
        # -------------------------------------------------------------

        dimension = None
        context = None
        option = None

        if component == TwinComponent.PREFERENCE:

            if decision.option is None:
                raise ValueError(
                    "Preference resolution requires option."
                )

            option = decision.option

        # -------------------------------------------------------------
        # NEW
        # -------------------------------------------------------------

        if decision.status == ResolutionStatus.NEW:

            if decision.entity_name is None:
                raise ValueError(
                    "NEW resolution requires entity_name."
                )

            if decision.direction is None:
                raise ValueError(
                    "NEW resolution requires direction."
                )

            if decision.strength is None:
                raise ValueError(
                    "NEW resolution requires strength."
                )

            if component == TwinComponent.PREFERENCE:

                if decision.dimension is None:
                    raise ValueError(
                        "NEW preference resolution requires dimension."
                    )

                if decision.context is None:
                    raise ValueError(
                        "NEW preference resolution requires context."
                    )

                valid_options = {
                    item.value
                    for item in PREFERENCE_OPTION_ENUMS[
                        decision.dimension
                    ]
                }

                if decision.option not in valid_options:
                    raise ValueError(
                        f"Invalid preference option "
                        f"'{decision.option}' for dimension "
                        f"'{decision.dimension.value}'."
                    )

                dimension = decision.dimension
                context = decision.context

            return ResolvedEvidence(
                memory_id=memory.memory_id,
                component=component,
                status=ResolutionStatus.NEW,
                entity_id=None,
                entity_name=decision.entity_name,
                dimension=dimension,
                context=context,
                option=option,
                direction=decision.direction,
                strength=decision.strength,
                resolution_confidence=decision.confidence,
                reason=decision.reason,
            )

        # -------------------------------------------------------------
        # EXISTING
        # -------------------------------------------------------------

        if decision.status == ResolutionStatus.EXISTING:

            if decision.candidate_index is None:
                raise ValueError(
                    "EXISTING resolution requires candidate_index."
                )

            if not (
                0
                <= decision.candidate_index
                < len(candidates)
            ):
                raise ValueError(
                    "Gemini returned an invalid candidate_index."
                )

            if decision.direction is None:
                raise ValueError(
                    "EXISTING resolution requires direction."
                )

            if decision.strength is None:
                raise ValueError(
                    "EXISTING resolution requires strength."
                )

            candidate = candidates[
                decision.candidate_index
            ]

            if component == TwinComponent.PREFERENCE:

                if candidate.preference_dimension is None:
                    raise ValueError(
                        "Preference candidate is missing dimension."
                    )

                if candidate.preference_context is None:
                    raise ValueError(
                        "Preference candidate is missing context."
                    )

                if candidate.preference_options is None:
                    raise ValueError(
                        "Preference candidate is missing valid options."
                    )

                if decision.option not in candidate.preference_options:
                    raise ValueError(
                        f"Invalid preference option "
                        f"'{decision.option}'. "
                        f"Valid options are: "
                        f"{candidate.preference_options}"
                    )

                dimension = candidate.preference_dimension
                context = candidate.preference_context

            return ResolvedEvidence(
                memory_id=memory.memory_id,
                component=component,
                status=ResolutionStatus.EXISTING,
                entity_id=candidate.entity_id,
                entity_name=candidate.name,
                dimension=dimension,
                context=context,
                option=option,
                direction=decision.direction,
                strength=decision.strength,
                resolution_confidence=decision.confidence,
                reason=decision.reason,
            )

        raise ValueError(
            f"Unsupported resolution status: "
            f"{decision.status}"
        )

    # =================================================================
    # Candidate Formatting
    # =================================================================

    @staticmethod
    def _format_candidates(
        candidates: list[TwinCandidate],
    ) -> str:
        """
        Convert candidates into a compact representation
        suitable for the Gemini prompt.
        """

        if not candidates:
            return "No existing candidates were retrieved."

        formatted = []

        for index, candidate in enumerate(candidates):

            text = (
                f"Candidate {index}:\n"
                f"Component: {candidate.component.value}\n"
                f"Name: {candidate.name}\n"
                f"Description: "
                f"{candidate.description or 'None'}\n"
                f"Semantic similarity: "
                f"{candidate.similarity:.3f}"
            )

            if candidate.component == TwinComponent.PREFERENCE:

                text += (
                    f"\nPreference dimension: "
                    f"{candidate.preference_dimension.value}"
                    f"\nPreference context: "
                    f"{candidate.preference_context.value}"
                    f"\nValid options: "
                    f"{candidate.preference_options}"
                )

            formatted.append(text)

        return "\n\n".join(formatted)

    # =================================================================
    # Preference Vocabulary
    # =================================================================

    @staticmethod
    def _format_preference_dimensions() -> str:
        """
        Return all valid preference dimensions and their options.
        """

        lines = []

        for dimension, enum_cls in PREFERENCE_OPTION_ENUMS.items():

            options = [
                option.value
                for option in enum_cls
            ]

            lines.append(
                f"- {dimension.value}: {options}"
            )

        return "\n".join(lines)

    @staticmethod
    def _format_learning_contexts() -> str:
        """
        Return all valid learning contexts.
        """

        return "\n".join(
            f"- {context.value}"
            for context in LearningContext
        )

    # =================================================================
    # Twin Item Helpers
    # =================================================================

    @staticmethod
    def _get_component(
        item: TwinItem,
    ) -> TwinComponent:
        """
        Determine which Twin component a searchable item belongs to.
        """

        if isinstance(item, Skill):
            return TwinComponent.SKILL

        if isinstance(item, Knowledge):
            return TwinComponent.KNOWLEDGE

        if isinstance(item, Interest):
            return TwinComponent.INTEREST

        if isinstance(item, Preference):
            return TwinComponent.PREFERENCE

        raise TypeError(
            f"Unsupported Twin item type: "
            f"{type(item).__name__}"
        )

    @staticmethod
    def _candidate_from_item(
        item: TwinItem,
        similarity: float,
    ) -> TwinCandidate:
        """
        Convert an actual Twin model into a resolver candidate.

        Entity IDs always come from the StudentTwin.
        """

        if isinstance(item, Skill):

            return TwinCandidate(
                component=TwinComponent.SKILL,
                entity_id=item.skill_id,
                name=item.name,
                description=item.description,
                similarity=similarity,
            )

        if isinstance(item, Knowledge):

            return TwinCandidate(
                component=TwinComponent.KNOWLEDGE,
                entity_id=item.knowledge_id,
                name=item.title,
                description=item.description,
                similarity=similarity,
            )

        if isinstance(item, Interest):

            return TwinCandidate(
                component=TwinComponent.INTEREST,
                entity_id=item.interest_id,
                name=item.topic,
                description=item.description,
                similarity=similarity,
            )

        if isinstance(item, Preference):

            return TwinCandidate(
                component=TwinComponent.PREFERENCE,
                entity_id=item.preference_id,
                name=(
                    f"{item.dimension.value} "
                    f"({item.context.value})"
                ),
                description=None,
                similarity=similarity,
                preference_dimension=item.dimension,
                preference_context=item.context,
                preference_options=list(
                    item.affinities.keys()
                ),
            )

        raise TypeError(
            f"Unsupported Twin item type: "
            f"{type(item).__name__}"
        )