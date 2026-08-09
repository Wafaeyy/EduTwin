from src.knowledge_graph.knowledge_graph import (
    KnowledgeNode,
    extract_concept,
    search_node,
    get_node_predecessors,
    G,
)

from src.retrieval.evidence import Evidence
from src.twin.enums import EvidenceSource


def knowledge_graph_retriever(query: str) -> list[Evidence]:

    concept = extract_concept(query)

    node_name = search_node(
        concept["concept"],
        concept["description"],
        False,
    )

    if node_name is None:
        return []

    retrieved = [
        G.nodes[node_name]["knowledgeNode"]
    ]

    retrieved.extend(
        get_node_predecessors(node_name)
    )

    evidence: list[Evidence] = []

    for node in retrieved:
        evidence.append(
            knowledge_to_evidence(node)
        )

    return evidence


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