from datetime import datetime,date

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
from src.knowledge_graph.knowledge_graph_updater import KnowledgeUpdater
from src.twin.profile import Profile
from src.twin.preference import Preference
from src.twin.knowledge import Knowledge
from src.twin.skill import Skill
from src.twin.interest import Interest
from src.twin.goal import Goal
from src.twin.enums import EducationStage,LearningContext,PreferenceDimension,GoalPriority,GoalStatus

from src.agents import AgentOrchestrator

class EduTwinService:

    def __init__(self):
        # Student's current Digital Twin
        profile = Profile(
                full_name= "teez kebera",
                university= "big ass",
                fied_of_study="AI",
                education_stage= EducationStage.UNDERGRAD_YEAR_2,
                email="test@gmail.com"
            )
        
        self.twin = StudentTwin(profile=profile)
        
        skill = Skill(
                name= "building AI models",
                description="use machine learning to build ai models",
                skill_level=0.5,
                confidence=0.3
            )
        
        knowledge = Knowledge(
                title="machine learning",
                description="hehe",
                mastery= 0.9,
                confidence= 0.6
            )
        
        interest = Interest(
                topic="cats",
                affinity=0.1,
                confidence=0.9
            )
        
        preference = Preference(
                dimension= PreferenceDimension.EXPLANATION_DEPTH,
                context= LearningContext.GENERAL,
                affinities= {"Short":0.5,
                                "Medium": 0.7,
                                "Detailed": 0.3}
            )
        goal = Goal(
        title="Build Strong Machine Learning Foundations",
        description=(
        "Develop a solid understanding of machine learning fundamentals, "
        "including supervised learning, model evaluation, feature engineering, "
        "and common algorithms, and apply them in practical projects."
        ),
        priority=GoalPriority.HIGH,
        status=GoalStatus.ACTIVE,
        progress=25,
        target_completion_date=date(2026, 12, 31),
)
        self.twin.skills[skill.skill_id] = skill
        self.twin.knowledge[knowledge.knowledge_id] = knowledge
        self.twin.interests[interest.interest_id] = interest
        self.twin.preferences[preference.preference_id] = preference
        self.twin.goals[goal.goal_id] = goal
        
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
        knowledge_updater = KnowledgeUpdater()
        component_updaters = [
            interest_updater,
            skill_updater,
            preference_updater,
            knowledge_updater
        ]

        self.twin_updater = TwinUpdater(
            component_updaters=component_updaters
        )

        self.resolver = TwinEntityResolver(
            twin_store=self.twin_store
        )
        
        self.agent_orchestrator = AgentOrchestrator()

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

        agent_result = self.agent_orchestrator.process(query=query, brief=brief, twin=self.twin)
        agent_answer = agent_result.reply
        
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
        
    def get_profile(self) -> Profile:
        """
        Return the student's current profile.
        """
        return self.twin.profile

    def update_profile(self, profile: Profile) -> Profile:
        """
        Replace the student's profile with an explicitly
        edited profile from the user.

        Profile edits made directly by the learner do not
        go through the AI Twin Updater.
        """
        self.twin.profile = profile
        self.twin.last_updated = datetime.now()

        return self.twin.profile
    
    def get_twin(self) -> StudentTwin:
        """
        Return the student's current Digital Twin.
        """
        return self.twin