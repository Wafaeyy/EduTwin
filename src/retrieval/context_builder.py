"""
context_builder.py

Builds the context supplied to AI agents.

The ContextBuilder formats retrieved evidence into a structured context
that is easy for an LLM to consume.

It performs no retrieval, ranking, or filtering.
"""

from collections import defaultdict

from src.retrieval.evidence import Evidence
from src.twin.enums import EvidenceSource


class ContextBuilder:
    """
    Builds the final context passed to AI agents.
    """

    #####################################################################
    # Public API
    #####################################################################

    def build(
        self,
        evidence: list[Evidence],
    ) -> str:
        """
        Build the final agent context.
        """

        grouped = self._group_evidence(evidence)

        sections: list[str] = []

        if EvidenceSource.TWIN in grouped:
            sections.append(
                self._build_section(
                    "STUDENT PROFILE & TWIN",
                    grouped[EvidenceSource.TWIN],
                )
            )

        if EvidenceSource.MEMORY in grouped:
            sections.append(
                self._build_section(
                    "RELEVANT MEMORIES",
                    grouped[EvidenceSource.MEMORY],
                )
            )

        if EvidenceSource.GRAPH in grouped:
            sections.append(
                self._build_section(
                    "RELEVANT KNOWLEDGE",
                    grouped[EvidenceSource.GRAPH],
                )
            )

        return "\n\n".join(sections)

    #####################################################################
    # Private Helpers
    #####################################################################

    def _group_evidence(
        self,
        evidence: list[Evidence],
    ) -> dict[EvidenceSource, list[Evidence]]:
        """
        Group evidence by source while preserving order.
        """

        grouped = defaultdict(list)

        for item in evidence:
            grouped[item.source].append(item)

        return grouped

    def _build_section(
        self,
        title: str,
        evidence: list[Evidence],
    ) -> str:
        """
        Build one context section.
        """

        lines = [
            "=" * 70,
            title,
            "=" * 70,
            "",
        ]

        for item in evidence:
            lines.append(item.content)
            lines.append("")

        return "\n".join(lines)