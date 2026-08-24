from src.retrieval.context_builder import ContextBuilder
from src.retrieval.retrieval_orchestrator import RetrievalOrchestrator
from src.retrieval.memory_retriever import MemoryRetriever, MemoryStore
from src.retrieval.twin_retriever import TwinRetriever, TwinStore, StudentTwin

from src.memory.memory_decision import MemoryDecision

from src.updater.updater import TwinUpdater
from src.updater.interest_updater import InterestUpdater
from src.updater.preference_updater import PreferenceUpdater
from src.updater.skill_updater import SkillUpdater
from src.updater.resolver import TwinEntityResolver

from src.twin.profile import Profile
from src.twin.enums import EducationStage

from src.agents.recommendation_system.orchestrator_interface import (
    recommend_text,
)

class EduTwinService:

    def __init__(self):
        # Student's current Digital Twin
        profile = Profile(
                full_name= "teez kebera",
                university= "big ass",
                fied_of_study="AI",
                education_stage= EducationStage.UNDERGRAD_YEAR_2,
            )
        
        self.twin = StudentTwin(profile=profile)

        # Retrieval components
        self.context_builder = ContextBuilder()

        self.memory_store = MemoryStore()
        self.memory_retriever = MemoryRetriever(
            memory_store=self.memory_store
        )

        self.twin_store = TwinStore()
        self.twin_retriever = TwinRetriever(
            twin_store=self.twin_store
        )

        self.retrieval_orchestrator = RetrievalOrchestrator(
            memory_retriever=self.memory_retriever,
            twin_retriever=self.twin_retriever,
        )

        # Memory system
        self.memory_decision = MemoryDecision(
            memory_store=self.memory_store
        )

        # Twin updater
        interest_updater = InterestUpdater()
        skill_updater = SkillUpdater()
        preference_updater = PreferenceUpdater()

        component_updaters = [
            interest_updater,
            skill_updater,
            preference_updater,
        ]

        self.twin_updater = TwinUpdater(
            component_updaters=component_updaters
        )

        self.resolver = TwinEntityResolver(
            twin_store=self.twin_store
        )

    def process_message(self, query: str):
        """
        Process one user interaction through the EduTwin pipeline.

        Current pipeline:

        User Query
            ↓
        Retrieval
            ↓
        Context Builder
            ↓
        Agent
            ↓
        Memory Decision
            ↓
        Twin Updater
        """

        # -----------------------------------------
        # 1. Retrieve relevant evidence
        # -----------------------------------------

        retrieval_result = self.retrieval_orchestrator.retrieve(
            query=query,
            student=self.twin,
        )

        # -----------------------------------------
        # 2. Build context for the agent
        # -----------------------------------------

        brief = self.context_builder.build(
            retrieval_result
        )

        # -----------------------------------------
        # 3. Agent
        # -----------------------------------------
        #
        # The actual agent will be connected here.
        #
        # Example later:
        #
        # agent_answer = agent(brief)
        #

        agent_answer = recommend_text(briefing= brief)
        
        # -----------------------------------------
        # 4. Decide whether interaction becomes
        #    a memory
        # -----------------------------------------

        memory = self.memory_decision.process_interaction(
            user_message=query,
            assistant_message=agent_answer,
        )

        # -----------------------------------------
        # 5. Resolve evidence for Twin update
        # -----------------------------------------

        if memory:
            resolved_evidence = self.resolver.resolve(
                student=self.twin,
                memory=memory,
            )

            # -------------------------------------
            # 6. Update the Digital Twin
            # -------------------------------------

            self.twin_updater.update(
                self.twin,
                resolved_evidence,
            )

        return {
            "answer": agent_answer,
            "brief": brief,
            "memory_created": memory is not None,
            "twin": self.twin,
        }