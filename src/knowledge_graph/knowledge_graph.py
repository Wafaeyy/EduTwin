import networkx as nx
import matplotlib.pyplot as mtl
from twin.knowledge import Knowledge
from twin.skill import Skill
import json
import numpy as np
from google import genai
from pydantic import BaseModel ,  Field


import os
os.environ["GOOGLE_API_KEY"] = "" ##free ver
client = genai.Client()


class YesNoResponse(BaseModel):
    answer : bool =Field(
        description="True if the concepts refer to the same educational concept, otherwise false."
    )    
def ask_yes_no (question:str)-> bool:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=question,
        config={
            "response_mime_type":"application/json",
            "response_schema":YesNoResponse
            }
    ).parsed
    return response.answer

class prerequisites (BaseModel):
    list_prerequisites: list[str]=Field(
        description="list of main prerequisites IF EXISTS for the given concept"
    )
def get_prerequisites(concept:str , description :str)->  list[str]:
    response= client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""You are an educational knowledge graph assistant.
            
            Given the concept below, identify the essential prerequisite concepts that someone should understand before learning it.
            
            Rules:
            - Return between 0 and 5 prerequisite concepts.
            - Return only direct, fundamental prerequisites.
            - If the concept requires no meaningful prerequisites, return an empty list.
            - Use canonical educational concept names (e.g. "Linear Algebra", "Functions", "Variables").
            - Do not include the concept itself.
            - Do not explain your reasoning.
            - Do not include duplicates.
            - The response must conform to the provided JSON schema.
            
            Concept:
            {concept}
            Description:
            {description}""",
        config={
            "response_mime_type":"application/json",
            "response_schema":prerequisites
        }
    ).parsed
    return response.list_prerequisites
    
class KnowledgeNode  :
    def __init__ (self , knowledge : Knowledge, embedding : list[float]):
        self.knowledge =knowledge
        self.embedding = embedding


def get_embedding (content :str) -> list[float]:
    result = client.models.embed_content(
    model="gemini-embedding-001",
        contents=content
    )

    embedding =result.embeddings[0].values
    return embedding



##extract the concept of the query in 1 or 2 words

def extract_concept(content :str)->dict[str , str]:

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
    

    return json.loads(response.text) #this turns it into a dictionary

G = nx.DiGraph()
#node = knowledgeNode()#useless btw, for testing 
#elist = [(1, 2), (2, 3), (1, 4), (4, 2)]
#G.add_edges_from(elist)
#G.add_node(
#        "nodeName",
#        node=node # all till here
#)
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



def search_node (name:str, description:str, create:bool):
    embed = get_embedding(name)
    highestSimi=-1
    node_highest=None
    for n in G.nodes:
        similarity=cosine_similarity(embed,G.nodes[n]["knowledgeNode"].embedding)
        if highestSimi<similarity: 
            highestSimi=similarity
            node_highest = n

        
    if highestSimi>= 0.95:
        return node_highest   
    elif highestSimi>= 0.85 :
        q=f"Is {node_highest} and {name} the same educational concept ?"
        if ask_yes_no(question=q):
            return node_highest
        else:
            if create:
                create_node(name=name, description=description,embedding=embed)
                add_prerequisites(name=name, description=description)
            return

    else :
        if create:
            create_node(name=name, description=description,embedding=embed)
            add_prerequisites(name=name, description=description)
        return


    #node = knowledgeNode(knowledge=Knowledge(),embedding=embed)

def create_node(name:str , description:str,embedding :list[float]):
    k=Knowledge(title= name ,description=description, mastery=0 ,confidence=0)
    
    kn=KnowledgeNode(knowledge=k,embedding= embedding) #TODO can use the embedding used for the search 
    G.add_node(
        name,
        knowledgeNode=kn,
    )

def add_prerequisites(name,description):
    listprere=get_prerequisites(concept=name , description=description)
    for p in listprere:
        n= search_node(p,"",False)
        if n != None:
            G.add_edge(n,name)
def get_node_predecessors(name:str)->list[KnowledgeNode]:
    L:list[KnowledgeNode] =[]
    for node in list(G.predecessors(name)):
        L.append(G.nodes[node]["knowledgeNode"])
    return L
    

def get_node_successors(name:str)->list[KnowledgeNode]:
    L:list[KnowledgeNode]=[]
    for node in list(G.successors(name)):
        L.append(G.nodes[node]["knowledgeNode"])
    return L
## TODO when creating a new node send to LLM to make 5-10 prerequisites cosine similarity to search (and save their embedding) if these already exist or make new ones and make edges inbetween 

## G.add_node(
##    "python",
##    mastery=0.82,
##    embedding=[0.13, 0.41, ...]
##)




nx.draw_spring(G)
mtl.show()




