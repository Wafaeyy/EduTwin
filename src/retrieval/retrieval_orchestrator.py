"""
retrieval_orchestrator.py

Coordinates the retrieval pipeline.

The RetrievalOrchestrator is the single entry point into the retrieval
layer. It first asks Gemini to determine which retrieval sources are
required, builds a RetrievalRequest, then invokes the corresponding
retrievers and aggregates all retrieved evidence.
"""

from google import genai
from pydantic import BaseModel, Field

from src.retrieval.memory_retriever import MemoryRetriever
from src.retrieval.evidence import Evidence
from src.retrieval.retrieval_request import RetrievalRequest
## TODO Graph
from src.retrieval.knowledge_retriever import GraphRetriever
from src.retrieval.twin_retriever import TwinRetriever
from src.twin.student import StudentTwin

# TODO ADD INTENT

class RetrievalPlan(BaseModel):
    """
    Gemini's retrieval planning decision.
    """

    retrieve_memory: bool = Field(
        description="Whether episodic memory retrieval is needed."
    )

    retrieve_twin: bool = Field(
        description="Whether Twin retrieval is needed."
    )

    retrieve_graph: bool = Field(
        description="Whether knowledge graph retrieval is needed."
    )

    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of items each retriever should return."
    )


class RetrievalOrchestrator:
    """
    Coordinates all retrieval sources.
    """

    def __init__(
        self,
        memory_retriever: MemoryRetriever,
        twin_retriever: TwinRetriever,
        graph_retriever: GraphRetriever,
    ):

        self.memory_retriever = memory_retriever
        self.twin_retriever = twin_retriever
        self.graph_retriever = graph_retriever

        self.gemini = genai.Client()

    #####################################################################
    # Public API
    #####################################################################

    def retrieve(
        self,
        student: StudentTwin,
        query: str,
    ) -> list[Evidence]:
        """
        Retrieve all relevant evidence for a user query.
        """

        request = self._build_request(query)

        evidence: list[Evidence] = []

        if request.retrieve_memory:
            evidence.extend(
                self.memory_retriever.retrieve(request)
            )

        if request.retrieve_twin:
            evidence.extend(
                self.twin_retriever.retrieve(
                    student=student,
                    request=request,
                )
            )

        if request.retrieve_graph:
            evidence.extend(
                self.graph_retriever.retrieve(request)
            )

        return evidence

    #####################################################################
    # Private Helpers
    #####################################################################

    def _build_request(
        self,
        query: str,
    ) -> RetrievalRequest:
        """
        Uses Gemini to determine which retrieval sources are needed.
        """

        prompt = f"""
You are planning retrieval for an AI Digital Twin.

Given the user's query, determine which information sources are needed.

Sources:

Memory:
- Past conversations
- Experiences
- Previous preferences
- Historical events

Twin:
- Current goals
- Current skills
- Current knowledge
- Current interests
- Current preferences
- Student profile

Knowledge Graph:
- Domain knowledge
- Concept relationships
- Prerequisites

Return ONLY the structured response.

User Query:
{query}
"""

        response = self.gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": RetrievalPlan,
            },
        )

        plan = response.parsed

        return RetrievalRequest(
            query=query,
            top_k=plan.top_k,
            retrieve_memory=plan.retrieve_memory,
            retrieve_twin=plan.retrieve_twin,
            retrieve_graph=plan.retrieve_graph,
        )
        
        ##plan not known check that