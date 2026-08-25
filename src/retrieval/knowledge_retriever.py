#from src.knowledge_graph.knowledge_graph import (
#    KnowledgeNode,
#    extract_concept,
#    search_node,
#    get_node_predecessors,
#    G,
#)
#
#from src.retrieval.evidence import Evidence
#from src.twin.enums import EvidenceSource
#
#
#def knowledge_graph_retriever(query: str) -> list[Evidence]:
#
#    concepts = extract_concept(query)
#    evidence: list[Evidence] = []
#    seen = set()
#
#    for c in concepts:
#        node_name = search_node(c["concept"], c["description"], create=False)
#        if node_name is None or node_name in seen:
#            continue
        #
#        seen.add(node_name)
#        evidence.append(knowledge_to_evidence(G.nodes[node_name]["knowledgeNode"]))
#
#        for p in get_node_predecessors(node_name):
#            if p.knowledge.title not in seen:
#                seen.add(p.knowledge.title)
#                evidence.append(knowledge_to_evidence(p))
#
#    return evidence
from typing import Optional
from src.knowledge_graph.knowledge_graph import KnowledgeGraph, KnowledgeNode, extract_concept
from src.retrieval.evidence import Evidence
from src.twin.enums import EvidenceSource


class KnowledgeGraphRetriever:
    """
    Object responsible for querying the student's KnowledgeGraph 
    and returning structured Evidence for the Twin.
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        # Injected dependency: No more floating global G!
        self.kg = knowledge_graph

    def retrieve(self, query: str) -> list[Evidence]:
        """Extracts concepts and returns the neighborhood evidence."""
        concepts = extract_concept(query)
        evidence: list[Evidence] = []
        seen = set()

        for c in concepts:
            # Call methods on self.kg instead of loose functions
            node_name = self.kg.search_node(c["concept"], c["description"], create=False)

            if node_name is None or node_name in seen:
                continue

            seen.add(node_name)
            node = self.kg.get_node(node_name)
            if node:
                evidence.append(self._to_evidence(node, "Target Concept"))

            # 1. Prerequisites (Predecessors)
            for p in self.kg.get_predecessors(node_name):
                if p.knowledge.title not in seen:
                    seen.add(p.knowledge.title)
                    evidence.append(self._to_evidence(p, f"Prerequisite of {node_name}"))

            # 2. Advanced applications (Successors)
            for s in self.kg.get_successors(node_name):
                if s.knowledge.title not in seen:
                    seen.add(s.knowledge.title)
                    evidence.append(self._to_evidence(s, f"Advanced application of {node_name}"))

        return evidence

    @staticmethod
    def _to_evidence(node: KnowledgeNode, relationship: str) -> Evidence:
        k = node.knowledge
        return Evidence(
            source=EvidenceSource.GRAPH,
            content=(
                f"--- Educational Knowledge Graph: {relationship} ---\n"
                f"Topic: {k.title}\n"
                f"Description: {k.description}\n"
                f"Student Mastery: {k.mastery:.1%} (Confidence: {k.confidence:.1%})"
            ),
            reference_id=k.knowledge_id,
            metadata={
                "mastery": k.mastery,
                "confidence": k.confidence,
                "relationship": relationship,
            },
        )








def knowledge_to_evidence(
    node: KnowledgeNode,
) -> Evidence:

    k = node.knowledge

    return Evidence(
        source=EvidenceSource.GRAPH,
        content=(
            "Knowledge Graph\n"
            f"Topic: {k.title}\n"
            f"Description: {k.description}\n"
            f"Mastery: {k.mastery:.2f}\n"
            f"Confidence: {k.confidence:.2f}"
        ),
        reference_id=k.knowledge_id,
        metadata={
            "mastery": k.mastery,
            "confidence": k.confidence,
        },
    )