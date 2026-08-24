from src.twin.enums import PerformanceSignal
from pydantic import BaseModel, Field
from google import genai
from src.knowledge_graph.knowledge_graph import (G, KnowledgeNode, search_node,safe_generate_content )
import networkx as nx
import time
client = genai.Client()
import matplotlib.pyplot as mtl

SIGNAL_METRICS = {
    "DEMONSTRATED_CORRECT": {"quality": 1.0, "default_weight": 1.0},
    "SELF_EXPLANATION_CORRECT": {"quality": 0.8, "default_weight": 0.7},
    "SELF_REPORTED_SUCCESS": {"quality": 0.3, "default_weight": 0.2},
    "QUESTION_ASKING": {"quality": 0.0, "default_weight": 0.1},
    "SELF_REPORTED_CONFUSION": {"quality": -0.3, "default_weight": 0.3},
    "SELF_EXPLANATION_INCORRECT": {"quality": -0.8, "default_weight": 0.7},
    "DEMONSTRATED_FAILURE": {"quality": -1.0, "default_weight": 1.0},
}
def update_node (node_name:str, quality : float,weight:float):
    if node_name not in G.nodes:
        return
    kn : KnowledgeNode = G.nodes[node_name]["knowledgeNode"]
    delta_alpha=max(0, quality) * weight
    delta_beta =max(0,-quality) * weight
    kn.alpha+= delta_alpha
    kn.beta += delta_beta    
    kn.recalculate_metrics()
#def propagate_upstream_evidence(target_node: str, quality: float, weight: float, gamma_0: float = 0.3, decay_lambda: float = 0.5):
#    if quality <= 0:
#        return
#    for node in G.nodes:
#    # Measure distance along incoming prerequisite paths
#
#        if node == target_node:
#            continue
#        
#        # Check if node is an ancestor/prerequisite of target_node
#        if nx.has_path(G, node, target_node):
#            distance = nx.shortest_path_length(G, node, target_node)
#            
#            # Geometric decay formula: gamma_0 * lambda^(d-1)
#            attenuation = gamma_0 * (decay_lambda ** (distance - 1))
#            dampened_weight = weight * attenuation
#            
#            update_node(node, quality, dampened_weight)
class EvidenceObservation(BaseModel):
    concept_name: str = Field(description="The canonical name of the educational concept mentioned")
    concept_description: str = Field(description="Brief explanation of the concept")
    signal: PerformanceSignal = Field(description="The extracted performance signal classification")
    weight: float = Field(
        description="Weight/importance of the evidence from 0.1 (passing mention) to 1.0 (verified task/assessment)",
        ge=0.1, le=1.0
    )
class MultiEvidenceExtraction(BaseModel):
    observations: list[EvidenceObservation]
def extract_evidence_from_message(user_message: str) -> list[EvidenceObservation]:
    prompt = f"""Analyze the user's message and extract any implicit or explicsit educational performance signals.
Rules:
- Identify all educational concepts mentioned.
- Categorize each concept into the appropriate PerformanceSignal.
- Assign a weight from 0.1 (low confidence/casual statement) to 1.0 (high confidence/concrete attempt).
- Do not make up concepts that are not present in the message.
User Message:
{user_message}"""
    response =safe_generate_content(# client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": MultiEvidenceExtraction
        }
    ).parsed
    return response.observations
def process_user_observation(user_message: str):
    observations = extract_evidence_from_message(user_message)
    
    for obs in observations:
        # Search or create node in graph
        target_node = search_node(obs.concept_name, obs.concept_description, create=True)
        if not target_node:
            continue
            
        signal_key = obs.signal.name if hasattr(obs.signal, 'name') else str(obs.signal)
        metrics = SIGNAL_METRICS.get(signal_key)
        
        if metrics is None:
            print(f"⚠️ Unknown signal {signal_key!r} — skipping")
            continue
        quality = metrics["quality"]
        weight = obs.weight
        
        update_node(target_node, quality, weight)
        
        
def print_graph_state():
    """Helper function to print all graph nodes and their statistical metrics."""
    print("\n" + "=" * 60)
    print("CURRENT KNOWLEDGE GRAPH STATE")
    print("=" * 60)
    
    if len(G.nodes) == 0:
        print("Graph is currently empty.")
        return
    for node_name in G.nodes:
        kn: KnowledgeNode = G.nodes[node_name]["knowledgeNode"]
        k = kn.knowledge
        prereqs = list(G.predecessors(node_name))
        
        print(f"\n📌 Concept: {node_name}")
        print(f"   Prerequisites : {prereqs if prereqs else 'None'}")
        print(f"   Alpha (α)     : {kn.alpha:.2f} | Beta (β) : {kn.beta:.2f}")
        print(f"   Mastery (E[X]): {k.mastery:.2%}")
        print(f"   Confidence    : {k.confidence:.2%}")
    print("=" * 60 + "\n")
def visualize_graph():
    """Renders the graph layout at the end without blocking execution midway."""
    if len(G.nodes) == 0:
        return
    mtl.figure(figsize=(10, 6))
    pos = nx.spring_layout(G, k=1.5)
    nx.draw(
        G, pos,
        with_labels=True,
        node_color='skyblue',
        node_size=2500,
        font_size=10,
        font_weight='bold',
        arrows=True,
        arrowsize=20
    )
    mtl.title("Student Knowledge Graph")
    mtl.show()
if __name__ == "__main__":
    print("Initializing Knowledge Updater System...\n")
    
    test_messages = [
        "I've been studying Linear Algebra and practicing Matrix Multiplication all week.",
        "Today I attempted Gradient Descent for optimization, but I made a math mistake in the step.",
        "I finally combined Gradient Descent and Matrix Multiplication to build Linear Regression!"
    ]
    for idx, msg in enumerate(test_messages, start=1):
        print(f"\n--- Turn {idx}: Processing User Message ---")
        print(f'User: "{msg}"')
        
        process_user_observation(msg)
        print_graph_state()
        # Pause AFTER processing the turn, not before
        if idx < len(test_messages):
            print(" Pausing 10 seconds before next turn...")
            time.sleep(10)
    visualize_graph()