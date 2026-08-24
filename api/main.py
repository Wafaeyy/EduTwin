from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services.edutwin_service import EduTwinService


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


service = EduTwinService()

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


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    result = service.process_message(
        request.message
    )

    return ChatResponse(
        answer=result["answer"]
    )