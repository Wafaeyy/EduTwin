"""
twin_store.py

Persistent vector store for searchable Twin components.

TwinStore is responsible for:

- Indexing searchable Twin components.
- Generating embeddings.
- Persisting Twin items.
- Updating a student's search index.
- Performing semantic retrieval.

It does not modify the StudentTwin itself.
"""

from uuid import UUID

import chromadb
from google import genai

from src.twin.interest import Interest
from src.twin.knowledge import Knowledge
from src.twin.preference import Preference
from src.twin.skill import Skill
from src.twin.student import StudentTwin

TwinItem = Skill | Knowledge | Interest | Preference


class TwinStore:
    """
    Stores searchable Twin components inside ChromaDB.
    """

    def __init__(
        self,
        persist_directory: str = "./database/chroma",
        collection_name: str = "student_twin",
    ):

        self.client = chromadb.PersistentClient(path=persist_directory)

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

        self.gemini = genai.Client()

    #####################################################################
    # Public API
    #####################################################################

    def index_student(
        self,
        student: StudentTwin,
    ) -> None:
        """
        Index every searchable Twin component.
        """

        self.delete_student(student.twin_id)

        for skill in student.skills.values():
            self._add_item(
                twin_id=student.twin_id,
                item_id=skill.skill_id,
                item_type="skill",
                searchable_text=self._skill_to_document(skill),
                document=skill.model_dump_json(),
            )

        for knowledge in student.knowledge.values():
            self._add_item(
                twin_id=student.twin_id,
                item_id=knowledge.knowledge_id,
                item_type="knowledge",
                searchable_text=self._knowledge_to_document(knowledge),
                document=knowledge.model_dump_json(),
            )

        for interest in student.interests.values():
            self._add_item(
                twin_id=student.twin_id,
                item_id=interest.interest_id,
                item_type="interest",
                searchable_text=self._interest_to_document(interest),
                document=interest.model_dump_json(),
            )

        for preference in student.preferences.values():
            self._add_item(
                twin_id=student.twin_id,
                item_id=preference.preference_id,
                item_type="preference",
                searchable_text=self._preference_to_document(preference),
                document=preference.model_dump_json(),
            )

    def update_student(
        self,
        student: StudentTwin,
    ) -> None:
        """
        Rebuild a student's search index.
        """

        self.index_student(student)

    def delete_student(
        self,
        twin_id: UUID,
    ) -> None:
        """
        Remove all indexed Twin items belonging to a student.
        """

        self.collection.delete(
            where={"twin_id": str(twin_id)}
        )

    def search(
        self,
        twin_id: UUID,
        query: str,
        top_n: int = 50,
    ) -> list[tuple[TwinItem, float]]:
        """
        Perform semantic search over a student's Twin.
        """

        query_embedding = self._generate_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_n,
            where={"twin_id": str(twin_id)},
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        model_map = {
            "skill": Skill,
            "knowledge": Knowledge,
            "interest": Interest,
            "preference": Preference,
        }

        retrieved = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        ):

            model = model_map[metadata["type"]]

            item = model.model_validate_json(document)

            similarity = 1.0 / (1.0 + distance)

            retrieved.append((item, similarity))

        return retrieved

    #####################################################################
    # Private Helpers
    #####################################################################

    def _add_item(
        self,
        twin_id: UUID,
        item_id: UUID,
        item_type: str,
        searchable_text: str,
        document: str,
    ) -> None:

        embedding = self._generate_embedding(searchable_text)

        self.collection.add(
            ids=[str(item_id)],
            documents=[document],
            embeddings=[embedding],
            metadatas=[{
                "twin_id": str(twin_id),
                "type": item_type,
            }]
        )

    def _generate_embedding(
        self,
        text: str,
    ) -> list[float]:

        response = self.gemini.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )

        return response.embeddings[0].values

    @staticmethod
    def _skill_to_document(skill: Skill) -> str:

        return (
            f"Skill: {skill.name}. "
            f"Level: {skill.skill_level:.2f}. "
            f"Confidence: {skill.confidence:.2f}."
        )

    @staticmethod
    def _knowledge_to_document(
        knowledge: Knowledge,
    ) -> str:

        return (
            f"Knowledge: {knowledge.title}. "
            f"Mastery: {knowledge.mastery:.2f}."
        )

    @staticmethod
    def _interest_to_document(
        interest: Interest,
    ) -> str:

        return (
                    f"Interest: {interest.topic}. "
                    f"Affinity: {interest.affinity:.2f}."
                    f"Confidence: {interest.confidence:.2f}."
                )

    @staticmethod
    def _preference_to_document(
        preference: Preference,
    ) -> str:

        return (
                            f"Dimension: {preference.dimension}. "
                            f"Context: {preference.context}."
                            f"Affinities: {preference.affinities}."
                        )