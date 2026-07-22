"""
memory_decision.py

Determines whether an interaction should become a long-term memory.

Pipeline

Interaction
    ↓
Rule Filter
    ↓
Gemini Classification
    ↓
Memory Candidate
    ↓
Duplicate Detection
    ↓
MemoryStore
"""

import re

from google import genai
from pydantic import BaseModel, Field

from twin.enums import MemoryType
from src.memory.memory import Memory
from memory.memory_store import MemoryStore


class MemoryDecisionResponse(BaseModel):
    """
    Structured response expected from Gemini.
    """

    store: bool

    memory_type: MemoryType | None = None

    importance: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    content: str | None = None


class MemoryDecision:

    def __init__(self, memory_store: MemoryStore):

        self.memory_store = memory_store
        self.gemini = genai.Client()

        self.ignored_messages = {
            "hi",
            "hello",
            "hey",
            "thanks",
            "thank you",
            "ok",
            "okay",
            "bye",
            "goodbye"
        }

    ####################################################################
    # Public API
    ####################################################################

    def process_interaction(
        self,
        user_message: str,
        assistant_message: str
    ) -> bool:
        """
        Returns True if a new memory was stored.
        """

        if not self._passes_rule_filter(user_message):
            return False

        decision = self._ask_gemini(
            user_message,
            assistant_message
        )

        if not decision.store:
            return False

        memory = self._build_memory(decision)

        self.memory_store.add_memory(memory)

        return True

    ####################################################################
    # Rule Filter
    ####################################################################

    def _passes_rule_filter(
        self,
        message: str
    ) -> bool:

        cleaned = message.lower()

        cleaned = re.sub(
            r"[^\w\s]",
            "",
            cleaned
        )

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned
        ).strip()

        return cleaned not in self.ignored_messages

    ####################################################################
    # Gemini
    ####################################################################

    def _ask_gemini(
        self,
        user_message: str,
        assistant_message: str
    ) -> MemoryDecisionResponse:

        prompt = f"""
You are the Memory Decision module of EduTwin.

A memory represents durable information that improves future personalization.

Store memories only if they represent:

• Goals
• Preferences
• Interests
• Knowledge gained
• Skills demonstrated
• Significant educational events

Do NOT store:

• Greetings
• Small talk
• Thanks
• Temporary requests
• Simple factual questions
• Politeness

Summarize the interaction into ONE concise memory.

Interaction

User:
{user_message}

Assistant:
{assistant_message}
"""

        response = self.gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": MemoryDecisionResponse
            }
        )

        return response.parsed

    ####################################################################
    # Helpers
    ####################################################################

    def _build_memory(
        self,
        decision: MemoryDecisionResponse
    ) -> Memory:

        if (
            decision.memory_type is None
            or decision.importance is None
            or decision.content is None
        ):
            raise ValueError(
                "Incomplete MemoryDecision response."
            )

        return Memory(
            memory_type=decision.memory_type,
            importance=decision.importance,
            content=decision.content
        )