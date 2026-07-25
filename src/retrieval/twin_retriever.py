"""
twin_retriever.py

Retrieves relevant information from the learner's Digital Twin.

The TwinRetriever always injects a static learner profile and goals,
then retrieves semantically relevant Twin components from the TwinStore.
"""

from src.retrieval.evidence import Evidence
from src.retrieval.retrieval_request import RetrievalRequest
from src.twin.twin_store import TwinStore
from src.twin.interest import Interest
from src.twin.knowledge import Knowledge
from src.twin.preference import Preference
from src.twin.skill import Skill
from src.twin.student import StudentTwin
from src.twin.enums import EvidenceSource


TwinItem = Skill | Knowledge | Interest | Preference


class TwinRetriever:
    """
    Retrieves relevant Twin information for a query.
    """

    def __init__(
        self,
        twin_store: TwinStore,
    ):
        self.twin_store = twin_store

    #####################################################################
    # Public API
    #####################################################################

    def retrieve(
        self,
        student: StudentTwin,
        request: RetrievalRequest,
    ) -> list[Evidence]:
        """
        Retrieve relevant Twin information.
        """

        evidence = [
            self._build_static_context(student)
        ]

        results = self.twin_store.search(
            twin_id=student.twin_id,
            query=request.query,
            top_n=request.top_k,
        )

        for item, similarity in results:
            evidence.append(
                self._to_evidence(
                    item=item,
                    similarity=similarity,
                )
            )

        return evidence

    #####################################################################
    # Private Helpers
    #####################################################################

    def _build_static_context(
        self,
        student: StudentTwin,
    ) -> Evidence:
        """
        Build the static learner snapshot that is always injected.
        """

        goals = "\n".join(
            f"- {goal.title}"
            for goal in student.goals.values()
        )

        content = (
            "Student Profile\n"
            f"Name: {student.profile.full_name}\n"
            f"University: {student.profile.university}\n"
            f"Field of Study: {student.profile.fied_of_study}\n"
            f"Current Year: {student.profile.current_year}\n"
            f"Education Stage: {student.profile.education_stage}\n\n"
            "Current Goals\n"
            f"{goals}"
        )

        return Evidence(
            source=EvidenceSource.TWIN,
            content=content,
            score=1.0,
        )

    def _to_evidence(
        self,
        item: TwinItem,
        similarity: float,
    ) -> Evidence:
        """
        Convert a Twin item into Evidence.
        """

        return Evidence(
            source=EvidenceSource.TWIN,
            content=self._format_item(item),
            score=similarity,
        )

    def _format_item(
        self,
        item: TwinItem,
    ) -> str:
        """
        Convert a Twin item into an LLM-friendly text representation.
        """

        if isinstance(item, Skill):
            return (
                "Skill\n"
                f"Name: {item.name}\n"
                f"Level: {item.skill_level:.2f}\n"
                f"Confidence: {item.confidence:.2f}"
            )

        if isinstance(item, Knowledge):
            return (
                "Knowledge\n"
                f"Topic: {item.title}\n"
                f"Mastery: {item.mastery:.2f}"
            )

        if isinstance(item, Interest):
            return (
                "Interest\n"
                f"Name: {item.topic}\n"
                f"Affinity: {item.affinity}\n"
                f"Confidence: {item.confidence}\n"
            )

        if isinstance(item, Preference):
            return (
                "Preference\n"
                f"Dimension: {item.dimension}\n"
                f"Context: {item.context}\n"
                f"Affinities: {item.affinities}\n"
            )

        raise TypeError(f"Unsupported Twin item type: {type(item)}")