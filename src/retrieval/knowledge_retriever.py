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
from src.knowledge_graph.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeNode,
    extract_concept,
)
from src.retrieval.evidence import Evidence
from src.twin.enums import EvidenceSource


class KnowledgeGraphRetriever:
    """
    Retrieves knowledge-graph evidence relevant to a user query.

    The retriever works through the KnowledgeGraph abstraction
    rather than directly manipulating the underlying NetworkX graph.
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph

    def retrieve(self, query: str) -> list[Evidence]:
        """
        Extract concepts from the query and retrieve:

        1. The matching target concept.
        2. Its prerequisites.
        3. Its advanced concepts/applications.
        """

        concepts = extract_concept(query)

        evidence: list[Evidence] = []
        seen: set[str] = set()

        for concept in concepts:

            node_name = self.kg.search_node(
                name=concept["concept"],
                description=concept["description"],
                create=False,
            )

            if node_name is None:
                continue

            if node_name in seen:
                continue

            seen.add(node_name)

            # --------------------------------------------------
            # Target concept
            # --------------------------------------------------

            node = self.kg.G.nodes[node_name]["knowledgeNode"]

            evidence.append(
                self._to_evidence(
                    node,
                    "Target Concept",
                )
            )

            # --------------------------------------------------
            # Prerequisites
            # --------------------------------------------------

            for prerequisite in self.kg.get_node_predecessors(node_name):

                prerequisite_name = prerequisite.knowledge.title

                if prerequisite_name in seen:
                    continue

                seen.add(prerequisite_name)

                evidence.append(
                    self._to_evidence(
                        prerequisite,
                        f"Prerequisite of {node_name}",
                    )
                )

            # --------------------------------------------------
            # Advanced concepts / applications
            # --------------------------------------------------

            for successor in self.kg.get_node_successors(node_name):

                successor_name = successor.knowledge.title

                if successor_name in seen:
                    continue

                seen.add(successor_name)

                evidence.append(
                    self._to_evidence(
                        successor,
                        f"Advanced application of {node_name}",
                    )
                )

        return evidence

    @staticmethod
    def _to_evidence(
        node: KnowledgeNode,
        relationship: str,
    ) -> Evidence:

        knowledge = node.knowledge

        return Evidence(
            source=EvidenceSource.GRAPH,
            content=(
                f"--- Educational Knowledge Graph: "
                f"{relationship} ---\n"
                f"Topic: {knowledge.title}\n"
                f"Description: {knowledge.description}\n"
                f"Student Mastery: {knowledge.mastery:.1%}\n"
                f"Confidence: {knowledge.confidence:.1%}"
            ),
            reference_id=knowledge.knowledge_id,
            metadata={
                "mastery": knowledge.mastery,
                "confidence": knowledge.confidence,
                "relationship": relationship,
            },
        )