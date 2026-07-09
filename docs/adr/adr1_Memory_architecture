Adopt a Multi-Layer Memory Architecture Inspired by Generative Agents
# ADR-0001: Adopt a Multi-Layer Memory Architecture for the AI Digital Twin

**Status:** Accepted

**Date:** 2026-07-09

---

# Context

One of the central challenges in educational AI is maintaining a persistent understanding of the learner over long periods of time.

Most current Large Language Model (LLM) applications are fundamentally stateless. Although conversation history can provide short-term context, it does not constitute a structured, evolving representation of the learner.

The EduTwin project aims to overcome this limitation by introducing a Digital Twin capable of maintaining long-term educational memory.

The paper **"Generative Agents: Interactive Simulacra of Human Behavior" (Park et al., CHI 2023)** demonstrates that persistent memory, combined with reflection and planning, enables AI agents to exhibit coherent long-term behavior.

While the paper targets autonomous social agents rather than educational systems, its memory architecture provides valuable design principles for EduTwin.

---

# Problem Statement

How should the EduTwin framework represent, store, retrieve, and evolve learner memories to support long-term educational personalization?

---

# Decision

EduTwin will adopt a **multi-layer memory architecture** inspired by the concepts presented in *Generative Agents* while adapting them to the educational domain.

The architecture will include:

- Persistent long-term learner memories.
- Selective memory retrieval.
- Memory importance scoring.
- Reflection-based knowledge synthesis.
- Continuous learner model updates.

The Digital Twin will serve as the central memory system shared by all AI agents.

---

# Adaptations for EduTwin

Rather than directly adopting the architecture proposed in *Generative Agents*, EduTwin introduces several domain-specific modifications.

| Generative Agents | EduTwin |
|-------------------|----------|
| Social memories | Educational memories |
| Daily plans | Learning plans |
| NPC goals | Learning and career goals |
| Social interactions | Learning activities |
| Agent identity | Structured learner profile |
| Free-form memories | Structured learner memories with metadata |

These modifications ensure that the memory system aligns with educational personalization rather than autonomous social simulation.

---

# Architectural Principles

The memory architecture should satisfy the following principles:

## Persistent

Learner memories must persist across sessions.

---

## Selective

Only relevant memories should be retrieved during reasoning.

---

## Reflective

The system should periodically synthesize higher-level insights from accumulated learner experiences.

---

## Explainable

Retrieved memories should provide evidence supporting AI recommendations and decisions.

---

## Evolvable

The learner model should continuously evolve as new educational experiences occur.

---

# Alternatives Considered

## Alternative 1 — Conversation History Only

Use only previous chat history.

**Rejected**

Reason:

Conversation history lacks structure, scalability, and explicit learner modeling.

---

## Alternative 2 — Vector Memory Only

Store all interactions as embeddings within a vector database.

**Rejected**

Reason:

Vector search alone cannot explicitly represent learner knowledge, goals, skills, or relationships.

---

## Alternative 3 — Structured Database Only

Maintain only structured learner attributes.

**Rejected**

Reason:

Structured representations cannot capture rich contextual experiences or nuanced interactions.

---

## Selected Approach

Combine:

- Structured learner model
- Long-term semantic memory
- Reflection
- Selective retrieval

This hybrid approach provides both structured reasoning and contextual recall.

---

# Consequences

## Advantages

- Supports lifelong personalization.
- Enables context-aware AI agents.
- Improves recommendation quality.
- Enhances explainability.
- Provides a shared memory system for multiple agents.

---

## Trade-offs

- Increased architectural complexity.
- Requires memory management policies.
- Reflection introduces additional computational cost.
- Memory consistency must be maintained across updates.

---

# Open Research Questions

Several important questions remain unresolved:

- How should memory importance be calculated?
- Should memory importance change over time?
- When should reflections be generated?
- Should reflections themselves become memories?
- How should conflicting memories be resolved?
- How should structured learner data interact with semantic memory?
- Should knowledge graph updates occur during reflection?

These questions will be investigated throughout subsequent research iterations.

---

# Supporting Literature

Primary reference:

Park, J. S., et al. (2023).

**Generative Agents: Interactive Simulacra of Human Behavior.**

Proceedings of the ACM Conference on Human Factors in Computing Systems (CHI 2023).

---

# Related Requirements

This ADR directly supports:

- FR-7 Long-Term Memory
- FR-8 Memory Retrieval
- FR-10 Explainability
- FR-11 Continuous Evolution
- FR-12 Multi-Agent Accessibility

Future requirements related to reflection and memory synthesis will extend this ADR.

---

# Future Revisions

This decision will be revisited after reviewing additional literature on:

- Retrieval-Augmented Generation (RAG)
- MemGPT
- Reflexion
- LongMem
- Knowledge Graph Memory
- Educational Digital Twins

Future ADRs may refine or supersede portions of this architecture as new evidence becomes available.