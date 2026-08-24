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

    concepts = extract_concept(query)
    evidence: list[Evidence] = []
    seen = set()

    for c in concepts:
        node_name = search_node(c["concept"], c["description"], create=False)
        if node_name is None or node_name in seen:
            continue

        seen.add(node_name)
        evidence.append(knowledge_to_evidence(G.nodes[node_name]["knowledgeNode"]))

        for p in get_node_predecessors(node_name):
            if p.knowledge.title not in seen:
                seen.add(p.knowledge.title)
                evidence.append(knowledge_to_evidence(p))

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