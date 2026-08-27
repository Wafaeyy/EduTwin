## IMPORTS
from src.retrieval.context_builder import ContextBuilder
from src.retrieval.retrieval_orchestrator import RetrievalOrchestrator
from src.retrieval.memory_retriever import MemoryRetriever,MemoryStore
from src.retrieval.twin_retriever import TwinRetriever,TwinStore,StudentTwin
from src.agents import AgentOrchestrator, route_and_execute_agent
from src.memory.memory_decision import MemoryDecision
from src.updater.updater import TwinUpdater
from src.updater.interest_updater import InterestUpdater
from src.updater.preference_updater import PreferenceUpdater
from src.updater.skill_updater import SkillUpdater
from src.knowledge_graph.knowledge_graph_updater import KnowledgeUpdater
from src.updater.resolver import TwinEntityResolver

## MAIN 
## TODO chats history to agent

def main():
    query = ""
    agent_answer = ""
    twin = StudentTwin()
    context_builder = ContextBuilder()
    memory_store = MemoryStore()
    memory_retriever = MemoryRetriever(memory_store= memory_store)
    twin_store = TwinStore()
    twin_retriever = TwinRetriever(twin_store= twin_store)
    retrieval_orchestrator = RetrievalOrchestrator(memory_retriever= memory_retriever, twin_retriever= twin_retriever)
    brief = context_builder.build(retrieval_orchestrator.retrieve(query= query, student= twin))
    ##send brief to agent
    agent_orchestrator = AgentOrchestrator()
    agent_result = agent_orchestrator.process(query=query, brief=brief, twin=twin)
    agent_answer = agent_result.reply
    memory_decision = MemoryDecision(memory_store= memory_store)
    memory = memory_decision.process_interaction(user_message= query, assistant_message= agent_answer)
    interest_updater = InterestUpdater()
    skill_updater = SkillUpdater()
    preference_updater = PreferenceUpdater()
    knowledge_updater = KnowledgeUpdater
    component_updaters = [interest_updater,skill_updater,preference_updater,knowledge_updater]
    twin_updater = TwinUpdater(component_updaters= component_updaters)
    resolver = TwinEntityResolver(twin_store= twin_store)
    resolved_evidence = resolver.resolve(student= twin, memory= memory)
    if memory:
        twin_updater.update(twin,resolved_evidence)
    

if __name__ == "__main__":
    main()