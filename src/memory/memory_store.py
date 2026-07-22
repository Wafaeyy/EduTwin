"""
memory_store.py

Persistent storage for learner memories using ChromaDB.

MemoryStore is responsible for:

- Formatting memories into searchable documents.
- Generating embeddings.
- Persisting memories.
- Retrieving memories by ID.
- Archiving memories.

It performs no semantic retrieval or ranking.
"""

from uuid import UUID

import chromadb
from google import genai

from src.memory.memory import Memory

DUPLICATE_THRESHOLD = 0.95

class MemoryStore:
    """
    Stores learner memories inside ChromaDB.
    """

    def __init__(
        self,
        persist_directory: str = "./database/chroma",
        collection_name: str = "memories",
    ):

        self.client = chromadb.PersistentClient(path=persist_directory)

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

        self.gemini = genai.Client()

    #####################################################################
    # Public API
    #####################################################################

    def add_memory(self, memory: Memory) -> bool:
        """
        Stores a memory if it does not already exist.

        Returns:
            True  -> Memory stored.
            False -> Duplicate memory detected.
        """

        document = self._memory_to_document(memory)

        embedding = self._generate_embedding(document)

        # Search for the most similar memory of the same type
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=1,
            where={
                "memory_type": memory.memory_type.value
            },
            include=["distances"]
        )

        # If there is already a similar memory, don't store it
        if results["ids"][0]:

            distance = results["distances"][0][0]

            similarity = 1.0 - distance

            if similarity >= DUPLICATE_THRESHOLD:
                return False

        # Store the new memory
        self.collection.add(
            ids=[str(memory.memory_id)],
            documents=[document],
            embeddings=[embedding],
            metadatas=[{
                "memory_type": memory.memory_type.value,
                "importance": memory.importance,
                "archived": False,
                "created_at": memory.created_at.isoformat()
            }]
        )

        return True

    def get_memory(self, memory_id: UUID):

        return self.collection.get(
            ids=[str(memory_id)]
        )

    def archive_memory(self, memory_id: UUID):

        result = self.collection.get(
            ids=[str(memory_id)],
            include=["metadatas"]
        )

        if not result["ids"]:
            return

        metadata = result["metadatas"][0]

        metadata["archived"] = True

        self.collection.update(
            ids=[str(memory_id)],
            metadatas=[metadata]
        )

    def list_memories(self):

        return self.collection.get()

    #####################################################################
    # Private Helpers
    #####################################################################

    def _memory_to_document(self, memory: Memory) -> str:
        """
        Converts a Memory into a semantically searchable document.
        """

        return (
            f"{memory.memory_type.value}: "
            f"{memory.content}"
        )

    def _generate_embedding(self, text: str) -> list[float]:
        """
        Generates a Gemini embedding for the supplied text.
        """

        response = self.gemini.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )

        return response.embeddings[0].values