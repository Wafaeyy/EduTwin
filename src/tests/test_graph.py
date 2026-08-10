from src.knowledge_graph.knowledge_graph import (
    G,
    create_node,
    search_node,
    extract_concept,
    get_embedding,
    cosine_similarity,
    get_prerequisites,
    get_node_predecessors,
    get_node_successors,
)

from src.retrieval.knowledge_retriever import (
    knowledge_graph_retriever
)


def reset_graph():
    G.clear()


# -------------------------
# Test new node insertion
# -------------------------



def test_duplicate_detection():

    reset_graph()


    first = search_node(
        "Machine Learning",
        "Learning algorithms from data",
        True
    )


    second = search_node(
        "Machine Learning",
        "Learning algorithms from data",
        True
    )


    assert first == second

    assert len(G.nodes)==1


    print("Duplicate detection works")



# -------------------------
# Test prerequisite edges
# -------------------------

def test_edges():

    reset_graph()


    search_node(
        "Statistics",
        "Collecting analyzing data",
        True
    )

    search_node(
        "Machine Learning",
        "Learning algorithms from data",
        True
    )


    print("Nodes:")
    print(list(G.nodes))


    print("Edges:")
    print(list(G.edges))


    assert len(G.edges)>0


    print("Edges created")



# -------------------------
# Test predecessor retrieval
# -------------------------

def test_predecessors():

    nodes = get_node_predecessors(
        "Machine Learning"
    )


    for n in nodes:
        print(n.knowledge.title)


    assert isinstance(nodes,list)



# -------------------------
# Test successor retrieval
# -------------------------

def test_successors():

    nodes = get_node_successors(
        "Machine Learning"
    )


    for n in nodes:
        print(n.knowledge.title)


    assert isinstance(nodes,list)



# -------------------------
# Test retrieval pipeline
# -------------------------

def test_retriever():

    reset_graph()


    search_node(
        "Machine Learning",
        "Learning algorithms from data",
        True
    )


    result = knowledge_graph_retriever(
        "I want to study machine learning"
    )


    print(result)


    assert len(result)>0


    print("Retriever works")



if __name__=="__main__":




    #test_duplicate_detection()

    test_edges()

    test_predecessors()

    test_successors()

    test_retriever()