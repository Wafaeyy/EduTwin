# ADR-0002: Adopt a Hybrid Retrieval Architecture for the AI Digital Twin

**Status:** Accepted

**Date:** 2026-07-09

---

# Context

Large Language Models (LLMs) possess strong reasoning capabilities but have limited access to persistent, evolving user-specific information. Retrieval-Augmented Generation (RAG) addresses this limitation by retrieving relevant external documents and incorporating them into the prompt before inference.

While RAG has proven effective for knowledge-intensive tasks, it was primarily designed to retrieve static external documents rather than represent a continuously evolving learner.

The EduTwin project requires retrieval mechanisms capable of reasoning over multiple sources of learner information, including structured learner profiles, long-term educational memories, semantic relationships, and inferred insights.

Consequently, a retrieval architecture designed solely around vector similarity is insufficient.

---

# Problem Statement

How should EduTwin retrieve learner information to provide accurate, personalized, explainable, and context-aware educational assistance?

---

# Decision

EduTwin will adopt a **Hybrid Retrieval Architecture** that integrates multiple retrieval strategies rather than relying solely on traditional vector-based Retrieval-Augmented Generation.

The retrieval process will combine:

- Structured learner profile retrieval
- Semantic long-term memory retrieval
- Knowledge Graph traversal
- Goal-aware filtering
- Metadata-aware ranking
- Reflection retrieval

These retrieval sources will be merged into a unified reasoning context before being provided to the language model.

---

# Motivation

Traditional RAG retrieves documents based primarily on semantic similarity.

Educational personalization requires considerably richer contextual reasoning.

When answering a learner's question, the system should consider:

- Current knowledge level
- Previously mastered concepts
- Learning objectives
- Career aspirations
- Recent learning activities
- Historical misconceptions
- Preferred learning style
- Reflections generated from previous interactions

No single retrieval mechanism captures all of this information effectively.

---

# Proposed Retrieval Pipeline

```
                User Query
                     │
                     ▼
          Query Understanding
                     │
                     ▼
          Retrieval Orchestrator
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
Structured Twin   Vector Memory   Knowledge Graph
 Retrieval         Retrieval        Retrieval
      │              │              │
      └──────────────┼──────────────┘
                     │
                     ▼
           Reflection Retrieval
                     │
                     ▼
           Context Aggregation
                     │
                     ▼
             Context Ranking
                     │
                     ▼
             Prompt Construction
                     │
                     ▼
               Language Model
                     │
                     ▼
           Reflection & Twin Update
```

---

# Retrieval Components

## 1. Structured Learner Retrieval

Purpose:

Retrieve explicit learner attributes.

Examples:

- Current knowledge level
- Skills
- Goals
- Interests
- Preferred learning style
- Career objectives

Advantages:

- Deterministic
- Explainable
- Efficient

---

## 2. Semantic Memory Retrieval

Purpose:

Retrieve relevant educational experiences using embedding similarity.

Examples:

- Previous study sessions
- Feedback
- Completed exercises
- User reflections
- Past conversations

Advantages:

- Captures contextual information
- Supports natural language reasoning
- Enables lifelong learning

---

## 3. Knowledge Graph Retrieval

Purpose:

Retrieve related concepts through graph traversal.

Examples:

- Topic prerequisites
- Skill dependencies
- Relationships between concepts
- Educational pathways

Advantages:

- Supports structured reasoning
- Improves recommendation quality
- Enables explainability

---

## 4. Reflection Retrieval

Purpose:

Retrieve higher-level insights generated from accumulated learner experiences.

Examples:

- Learning habits
- Persistent weaknesses
- Preferred study strategies
- Long-term progress summaries

Advantages:

- Reduces prompt size
- Improves long-term reasoning
- Captures latent learner characteristics

---

# Context Aggregation

Rather than passing every retrieved item directly to the LLM, EduTwin introduces a Context Aggregation stage.

This component:

- Removes duplicate information
- Resolves conflicts
- Prioritizes important memories
- Combines structured and unstructured knowledge
- Produces a coherent reasoning context

---

# Why Vanilla RAG Was Rejected

Traditional Retrieval-Augmented Generation relies primarily on semantic retrieval from external documents.

This approach has several limitations for educational personalization.

## Limitation 1

No persistent learner model.

---

## Limitation 2

No explicit representation of learner goals.

---

## Limitation 3

No representation of skills or competencies.

---

## Limitation 4

No reflective reasoning.

---

## Limitation 5

No knowledge graph integration.

---

## Limitation 6

No mechanism for continuous learner evolution.

---

# Alternatives Considered

## Alternative 1 — Standard Vector RAG

Retrieve only semantic memories.

**Rejected**

Reason:

Insufficient for personalized educational reasoning.

---

## Alternative 2 — Structured Retrieval Only

Retrieve only structured learner attributes.

**Rejected**

Reason:

Unable to capture rich educational experiences.

---

## Alternative 3 — Knowledge Graph Only

Retrieve only graph-based relationships.

**Rejected**

Reason:

Cannot represent nuanced interactions or conversational context.

---

## Selected Approach

Hybrid Retrieval combining:

- Structured data
- Semantic memory
- Knowledge Graph reasoning
- Reflection summaries

---

# Expected Benefits

- More accurate personalization
- Better educational recommendations
- Reduced hallucinations
- Improved explainability
- Better scalability
- Richer learner understanding
- Shared retrieval for multiple AI agents

---

# Trade-offs

Advantages:

- Rich contextual understanding
- Flexible architecture
- Supports future research

Disadvantages:

- Increased implementation complexity
- Multiple retrieval pipelines
- Higher computational cost
- More sophisticated ranking required

---

# Open Research Questions

Several questions remain unanswered and will be explored experimentally.

- How should retrieval scores from different sources be combined?
- How should structured and semantic information be weighted?
- Should learner goals influence retrieval ranking?
- Should reflection summaries replace older memories?
- How many memories should be retrieved?
- How should contradictory learner evidence be resolved?
- Should retrieval be personalized differently for each AI agent?

---

# Supporting Literature

Primary References

Lewis, P., et al. (2020).

**Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.**

NeurIPS 2020.

---

Park, J. S., et al. (2023).

**Generative Agents: Interactive Simulacra of Human Behavior.**

CHI 2023.

---

# Related Requirements

This ADR supports:

- FR-7 Long-Term Memory
- FR-8 Memory Retrieval
- FR-9 Knowledge Graph Integration
- FR-10 Explainability
- FR-11 Continuous Evolution
- FR-12 Multi-Agent Accessibility

Future requirements related to hybrid retrieval, ranking strategies, and reflection synthesis will extend this ADR.

---

# Impact on EduTwin Architecture

This ADR establishes the Retrieval Orchestrator as a core architectural component of EduTwin.

Rather than treating retrieval as a simple vector search operation, the system will perform multi-source context acquisition followed by context aggregation before invoking the language model.

This design transforms retrieval from a supporting utility into a central reasoning mechanism for personalized educational AI.

---

# Future Revisions

This decision will be revisited after reviewing literature on:

- Reflexion
- MemGPT
- LongMem
- GraphRAG
- Microsoft AutoGen
- CAMEL
- Educational Digital Twins
- Learner Modeling

Subsequent ADRs may refine retrieval ranking, memory prioritization, and agent-specific retrieval strategies based on empirical evaluation.