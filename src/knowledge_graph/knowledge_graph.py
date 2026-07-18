import networkx as nx
import matplotlib.pyplot as mtl
from twin.knowledge import Knowledge
from twin.skill import Skill
import json
import numpy as np
from google import genai

import os
os.environ["GOOGLE_API_KEY"] = "" ##free ver

class knowledgeNode  :
    def __init__ (self , knowledge : Knowledge, embedding : list[float]):
        self.knowledge =knowledge
        self.embedding = embedding


client = genai.Client()
def get_embedding (content :str) -> list[float]:
    result = client.models.embed_content(
     model="gemini-embedding-001",
        contents=content
    )

    embedding =result.embeddings[0].values
    return embedding



## TODO extract the concept of the query in 1 or 2 words

def Extract_concept(content :str)->dict[str , str]:

    prompt = f"""Extract the main educational concept from the user's message.

    Rules:
    - Return only the canonical educational concept.
    - Do not explain.
    - Return JSON only.

    Example:
    {{
        "concept": "Cooking",
        "descreption" : "the act of making food"
    }}

    User message:
    {content}"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    

    return json.loads(response) #this turns it into a dictionary

G = nx.Graph()
node = knowledgeNode()
elist = [(1, 2), (2, 3), (1, 4), (4, 2)]
G.add_edges_from(elist)
G.add_node(
    "nodeName",
    node=node
)
## TODO ## save its embedding and search through the whole graph
        ## cos sim > 0.95 reuse
        ## cos sim > 0.85 ask llm
        ## else create new node

def cosine_similarity(a,b):
        vector_a = np.array(a)
        vector_b = np.array(b)

        # Calculate dot product and norms
        dot_product = np.dot(vector_a, vector_b)
        norm_a = np.linalg.norm(vector_a)
        norm_b = np.linalg.norm(vector_b)

        # Compute similarity
        similarity = dot_product / (norm_a * norm_b)
        return similarity
def searchNode (name:str):
    embed = get_embedding(name)

    highestSimi=0

    for n in G.nodes:
        
        similarity=cosine_similarity(embed,n["node"].embedding)

        if highestSimi<similarity: 
            highestSimi=similarity
            nodeOfHighest = n["node"]
    if highestSimi>= 0.95:
        pass
        ##TODO reuse
    elif highestSimi>= 0.85:
        pass
        #TODO ask llm
    else :
        pass
        #TODO create newnode
    #node = knowledgeNode(knowledge=Knowledge(),embedding=embed)






## TODO when creating a new node send to LLM to make 5-10 prerequisites cosine similarity to search (and save their embedding) if these already exist or make new ones and make edges inbetween 




## G.add_node(
##    "python",
##    name="Python",
##    mastery=0.82,
##    embedding=[0.13, 0.41, ...]
##)




nx.draw_spring(G)
mtl.show()




