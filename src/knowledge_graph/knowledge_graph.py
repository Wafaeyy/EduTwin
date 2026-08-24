import networkx as nx
import matplotlib.pyplot as mtl
from src.twin.knowledge import Knowledge
from src.twin.skill import Skill
import json
import numpy as np
from google import genai
from pydantic import BaseModel,Field
import os
from dotenv import load_dotenv,find_dotenv
from typing import Optional

#load_dotenv(find_dotenv(),override=True)


import time
from google.genai.errors import ClientError








api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)



def safe_generate_content(model: str, contents: str, config: dict = None):
    """Wraps generate_content to automatically wait out 429 rate limits on Free Tier."""
    while True:
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
        except ClientError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("\n⚠️ Free Tier Rate Limit hit. Pausing 10 seconds before retrying...")
                time.sleep(10)
            else:
                raise e


def safe_embed_content(model: str, contents: str):
    """Wraps embed_content to automatically wait out 429 rate limits on Free Tier."""
    while True:
        try:
            return client.models.embed_content(
                model=model,
                contents=contents
            )
        except ClientError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("\n⚠️ Free Tier Rate Limit hit on Embeddings. Pausing 10 seconds before retrying...")
                time.sleep(10)
            else:
                raise e





class YesNoResponse(BaseModel):
    answer : bool =Field(
        description="True if the concepts refer to the same educational concept, otherwise false."
    )    
    
def ask_yes_no (question:str)-> bool:
    response =safe_generate_content(# client.models.generate_content(
        model="gemini-2.0-flash",
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
    response= safe_generate_content(#client.models.generate_content(
        model="gemini-2.0-flash",
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
    
class KnowledgeNode:
    def __init__(self, knowledge: Knowledge, embedding: list[float], alpha: float = 0.5, beta: float = 0.5):
        self.knowledge = knowledge
        self.embedding = embedding
        self.alpha = alpha
        self.beta = beta
        self.recalculate_metrics()

    # Theoretical maximum variance for Beta(0.5, 0.5) is Var_max = 0.125.
    # Confidence is defined as 1 - (Var / Var_max) = 1 - (8 * Var).
    def recalculate_metrics(self):
        # Posterior mean expected mastery: E[X] = alpha / (alpha + beta)
        self.knowledge.mastery = self.alpha / (self.alpha + self.beta)
        
        # Exact Beta variance calculation: Var(X) = (alpha * beta) / ((alpha + beta)^2 * (alpha + beta + 1))
        variance = (self.alpha * self.beta) / (((self.alpha + self.beta) ** 2) * (self.alpha + self.beta + 1))
        
        # Normalized variance-based confidence: ranges smoothly from 0.0 to 1.0 as variance approaches zero
        self.knowledge.confidence = max(0.0, min(1.0, 1.0 - (8.0 * variance)))

def get_embedding (content :str) -> list[float]:
    result = safe_embed_content(#client.models.embed_content(
    model="gemini-embedding-001",
        contents=content
    )

    embedding =result.embeddings[0].values
    return embedding



##extract the concept of the query in 1 or 2 words
class SingleConcept(BaseModel):
    concept: str = Field(description="Main educational concept from the user's message")
    description: str = Field(description="Brief explanation of the concept")
class MutliConcept(BaseModel):
    concepts: list[SingleConcept]
    
def extract_concept(content :str)->dict[str , str]:

    prompt = f"""Extract the main educational concept from the user's message.

    Rules:
    - Return only the canonical educational concept.
    - Do not explain.
    - Return JSON only.

    Example:
    {{
        "concept": "Cooking",
        "description" : "the act of making food"
    }}

    User message:
    {content}"""
    response =safe_generate_content(# client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={"response_mime_type":"application/json",
                "response_schema":MutliConcept}
    ).parsed
    

    return [c.model_dump() for c in response.concepts] #this turns it into a dictionary

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

        if norm_a == 0 or norm_b == 0:
            return 0.0
        similarity = dot_product / (norm_a * norm_b)
        return similarity


HIGH_THRESHOLD = 0.92
LOW_THRESHOLD  = 0.80
def search_node (name:str, description:str, create:bool,precomputed_embed: Optional[list[float]] = None):
    
   
    
    embed = precomputed_embed if precomputed_embed is not None else get_embedding( f"Title: {name}\nDescription: {description}")
    highestSimi=-1
    node_highest=None
    if len(G.nodes) == 0:
        if create:
            create_node(name=name, description=description, embedding=embed)
            add_prerequisites(name=name, description=description)
            return name
        return None
    
    canidates=[]

    for n in G.nodes:
        similarity=cosine_similarity(embed,G.nodes[n]["knowledgeNode"].embedding)
        canidates.append((n,similarity))
        #if highestSimi<similarity: 
        #    highestSimi=similarity
        #    node_highest = n
    canidates.sort(key=lambda x:x[1],reverse=True)
    print("search_node(", name, ", create=", create, ")",highestSimi)
    node_highest, highestSimi =canidates[0] 
    
    print(
    f"highest={highestSimi:.6f}, "
    f"high={HIGH_THRESHOLD}, "
    f"low={LOW_THRESHOLD}, "
    f"node={node_highest}"
    )
    
    if highestSimi>= HIGH_THRESHOLD:
        print("HIGH")
        return node_highest   
    
    
    for cani_node,cani_simi in canidates:
        if cani_simi< LOW_THRESHOLD :
            break
        print("LOW -> asking LLM")
        q= f"""
            Do these refer to the same concept for an educational prerequisite graph?
            Concept A: {cani_node}
            Concept B: {name}
            Answer only true or false.
            """
        if ask_yes_no(question=q):
            return cani_node
        #else:
        #    print("CREATE/NONE")
        #    if create:
        #        create_node(name=name, description=description,embedding=embed)
        #        add_prerequisites(name=name, description=description)
        #        return name
        #    return 
    if create:
        create_node(name=name, description=description,embedding=embed)
        add_prerequisites(name=name, description=description)
        return name
    return


    #node = knowledgeNode(knowledge=Knowledge(),embedding=embed)

def create_node(name: str, description: str, embedding: list[float]):
    k = Knowledge(title=name, description=description, mastery=0.5, confidence=0.0)
    kn = KnowledgeNode(knowledge=k, embedding=embedding, alpha=0.5, beta=0.5)
    G.add_node(
        name,
        knowledgeNode=kn,
    )

def add_prerequisites(name,description):
    listprere=get_prerequisites(
        concept=name,
        description=description
    )

    print("Prerequisites for", name)
    print(listprere)

    for p in listprere:
        n = search_node(p,"",False)

        print(
            "Searching prerequisite:",
            p,
            "Found:",
            n
        )

        if n != None:
            G.add_edge(n,name)
#def add_prerequisites(name,description):
#    listprere=get_prerequisites(concept=name , description=description)
#    for p in listprere:
#        n= search_node(p,"",False)
#        if n != None:
#            G.add_edge(n,name)
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








