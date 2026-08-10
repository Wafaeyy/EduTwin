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

from src.twin.enums import TwinComponent
from src.memory.memory import Memory
from src.memory.memory_store import MemoryStore


class MemoryDecisionResponse(BaseModel):
    """
    Structured response expected from Gemini.
    """

    store: bool

    importance: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    content: str | None = None

    affected_components: list[TwinComponent] = Field(
        default_factory=list
    )


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
    ) -> Memory | None:
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
            return None

        memory = self._build_memory(decision)

        self.memory_store.add_memory(memory)

        return memory

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

A memory represents durable information about the learner that
can improve future personalization.

Store memories only if they represent durable learner information
such as:

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
• Information that has no long-term value

If the interaction should be stored:

1. Summarize the learner-relevant information into ONE concise memory.
2. Assign an importance score from 0.0 to 1.0.
3. Identify which StudentTwin components may be affected.

The available Twin components are:

• knowledge
• skill
• interest
• preference
• goal

A memory may affect multiple components.

If the memory does not provide meaningful evidence for any
current Twin component, return an empty affected_components list.

Do not identify specific entities or IDs.
Entity resolution is handled by a separate module.

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
            decision.importance is None
            or decision.content is None
        ):
            raise ValueError(
                "Incomplete MemoryDecision response."
            )

        return Memory(
            content=decision.content,
            importance=decision.importance,
            affected_components=decision.affected_components
        )