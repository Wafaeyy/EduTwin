##import
from src.updater.base import ComponentUpdater
from src.knowledge_graph.knowledge_graph_updater import process_user_observation
class KnowledgeUpdater(ComponentUpdater):
    def update(self, student, evidence):
        return process_user_observation()