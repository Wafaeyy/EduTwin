from src.memory.memory import Memory
from src.memory.memory_store import MemoryStore
from src.retrieval.evidence import Evidence
from src.retrieval.retrieval_request import RetrievalRequest
from twin.enums import EvidenceSource
from datetime import datetime, timezone

RELEVANCE_WEIGHT = 0.6
IMPORTANCE_WEIGHT = 0.3
RECENCY_WEIGHT = 0.1
CANDIDATE_COUNT = 50

class MemoryRetriever:
    """
    Retrieves relevant memories for a retrieval request.
    """

    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store

    def retrieve(
        self,
        request: RetrievalRequest,
    ) -> list[Evidence]:
        """
        Retrieve relevant memories as Evidence.
        """

        candidates = self.memory_store.search(
            query=request.query,
            top_n= CANDIDATE_COUNT ,
        )

        candidates = self._apply_filters(candidates, request)
        candidates = self._rank_memories(candidates)

        return [
            self._memory_to_evidence(memory)
            for memory, _ in candidates[: request.top_k]
        ]

    def _apply_filters(
        self,
        candidates: list[tuple[Memory, float]],
        request: RetrievalRequest,
    ) -> list[tuple[Memory, float]]:
        """
        Apply optional retrieval constraints.
        """

        filtered = candidates

        if request.memory_types is not None:
            filtered = [
                (memory, similarity)
                for memory, similarity in filtered
                if memory.memory_type in request.memory_types
            ]

        if request.time_range is not None:
            filtered = [
                (memory, similarity)
                for memory, similarity in filtered
                if request.time_range.start
                <= memory.timestamp
                <= request.time_range.end
            ]

        if request.metadata_filters is not None:
            filtered = [
                (memory, similarity)
                for memory, similarity in filtered
                if all(
                    memory.metadata.get(key) == value
                    for key, value in request.metadata_filters.items()
                )
            ]

        return filtered

    def _rank_memories(self,candidates: list[tuple[Memory, float]]) -> list[tuple[Memory, float]]:
        """
        Rank candidate memories using a weighted combination of:
        - Semantic relevance
        - Importance
        - Recency
        """

        def calculate_score(memory: Memory, similarity: float) -> float:
            # Number of days since the memory was created
            days_old = (datetime.now(timezone.utc) - memory.timestamp).days

            # More recent memories receive a higher score.
            # Today -> 1.0
            # Yesterday -> 0.5
            # 7 days ago -> 0.125
            recency = 1 / (1 + days_old)

            return (
                RELEVANCE_WEIGHT * similarity
                + IMPORTANCE_WEIGHT * memory.importance
                + RECENCY_WEIGHT * recency
            )

        return sorted(
            candidates,
            key=lambda candidate: calculate_score(candidate[0], candidate[1]),
            reverse=True,
        )

    def _memory_to_evidence(
        self,
        memory: Memory,
    ) -> Evidence:
        """
        Convert a Memory into an Evidence object.
        """

        return Evidence(
            source=EvidenceSource.MEMORY,
            content=memory.content,
            reference_id=memory.memory_id,
            metadata={
                "memory_type": memory.memory_type,
                "importance": memory.importance,
                "timestamp": memory.timestamp,
            },
        )