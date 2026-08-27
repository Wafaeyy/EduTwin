from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services.edutwin_service import EduTwinService

from src.twin.profile import Profile

app = FastAPI(
    title="EduTwin API",
    description="Backend API for the EduTwin AI Digital Twin",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# For now we have ONE student.
# We will replace this with authentication later.
service = EduTwinService()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "EduTwin",
    }

@app.get("/twin/profile", response_model=Profile)
def get_profile():
    return service.get_profile()

@app.get("/twin")
def get_twin():

    twin = service.get_twin()

    return {
        "twin_id": str(twin.twin_id),

        "profile": twin.profile.model_dump(mode="json"),

        "goals": [
            goal.model_dump(mode="json")
            for goal in twin.goals.values()
        ],

        "preferences": [
            preference.model_dump(mode="json")
            for preference in twin.preferences.values()
        ],

        "knowledge": [
            knowledge.model_dump(mode="json")
            for knowledge in twin.knowledge.values()
        ],

        "skills": [
            skill.model_dump(mode="json")
            for skill in twin.skills.values()
        ],

        "interests": [
            interest.model_dump(mode="json")
            for interest in twin.interests.values()
        ],

        "created_at": twin.created_at.isoformat(),

        "last_updated": twin.last_updated.isoformat(),
    }

@app.get("/twin/knowledge-graph")
def get_knowledge_graph():
    student = service.twin

    nodes = []

    for node_name in student.graph.nodes:
        knowledge_node = student.graph.nodes[node_name]["knowledgeNode"]
        knowledge = knowledge_node.knowledge

        nodes.append({
            "id": node_name,
            "title": knowledge.title,
            "description": knowledge.description,
            "mastery": knowledge.mastery,
            "confidence": knowledge.confidence,
        })

    edges = []

    for source, target in student.graph.edges:
        edges.append({
            "source": source,
            "target": target,
        })

    return {
        "nodes": nodes,
        "edges": edges,
    }

@app.put("/twin/profile", response_model=Profile)
def update_profile(profile: Profile):
    return service.update_profile(profile)

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    result = service.process_message(
        request.message
    )

    return ChatResponse(
        answer=result["answer"]
    )