# Architecture Overview

> **Version 0.1 — Preliminary Architecture**

## Purpose

This document provides a high-level architectural vision for the EduTwin framework.

The architecture presented here is preliminary and will evolve throughout the literature review and experimental validation phases.

---

# High-Level Vision

The system consists of three major layers:

1. AI Agent Layer
2. Digital Twin Layer
3. AI Infrastructure Layer

The Digital Twin acts as the central source of truth shared by all AI agents.

---

# Major Components

## AI Agent Layer

Responsible for user-facing intelligence.

Candidate agents include:

- Study Coach
- Career Mentor
- Recommendation Engine
- Prediction Engine
- Explainability Module

---

## Digital Twin Layer

Responsible for representing the learner.

Candidate components include:

- User Model
- Long-Term Memory
- Knowledge Graph
- Learning Analytics
- Goal Representation

---

## Infrastructure Layer

Responsible for AI orchestration.

Candidate technologies:

- LangGraph
- LangChain
- OpenAI API
- ChromaDB
- NetworkX

---

# Preliminary System Flow

User Interaction

↓

AI Agent

↓

Digital Twin

↓

Memory Retrieval

↓

LLM Reasoning

↓

Personalized Response

↓

Digital Twin Update

---

# Architectural Principles

- Persistent learner modeling
- Modular design
- Explainability
- Shared Digital Twin
- Research-first implementation
- Extensibility

---

# Open Design Questions

The following questions remain unresolved and will be investigated through literature review:

- How should learner knowledge be represented?
- What memory architecture should be adopted?
- How should the Knowledge Graph interact with vector memory?
- Which Digital Twin attributes require explicit schemas?
- How should AI agents coordinate updates?

---

# Planned Revisions

This document will be updated after:

- Literature Review
- User Model Design
- Memory Architecture Design
- Knowledge Graph Design
- Internal API Specification


> **Version 0.2**

---

# Purpose

This document presents the current high-level architecture of the EduTwin framework.

Version 0.2 incorporates insights from the literature review, including persistent memory (Generative Agents) and Retrieval-Augmented Generation (RAG), while adapting these concepts to the educational domain.

The architecture remains research-oriented and is expected to evolve as additional literature and experiments are completed.

---

# Architectural Vision

EduTwin is centered around a continuously evolving **AI Digital Twin**.

Unlike traditional AI assistants that rely primarily on conversation history, the Digital Twin explicitly models the learner and serves as the shared source of truth for all AI agents.

Every interaction contributes to the evolution of the learner model.

---

# High-Level Architecture

```
                         User
                           │
                           ▼
                AI Agent Layer
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   Study Coach      Career Mentor     Recommendation Agent
                           │
                           ▼
               Retrieval Orchestrator
                           │
      ┌───────────┬─────────┼───────────┬───────────┐
      │           │         │           │
      ▼           ▼         ▼           ▼
Structured    Episodic   Knowledge   Reflection
 Profile      Memory       Graph       Memory
(Pydantic)   (ChromaDB)  (NetworkX)  (ChromaDB)
      │           │         │           │
      └───────────┴─────────┴───────────┘
                           │
                           ▼
                  Context Aggregator
                           │
                           ▼
                   Language Model
                           │
                           ▼
                  Reflection Engine
                           │
                           ▼
                 Digital Twin Updater
                           │
                           ▼
                     Updated Twin
```

---

# Core Components

## 1. AI Agent Layer

User-facing agents responsible for specialized educational tasks.

Examples:

- Study Coach
- Career Mentor
- Recommendation Agent
- Prediction Engine
- Explainability Agent

These agents never maintain independent learner state.

Instead, all agents interact with the shared Digital Twin.

---

## 2. Retrieval Orchestrator

Coordinates all retrieval operations before reasoning begins.

Responsibilities include:

- Query understanding
- Memory retrieval
- Learner profile retrieval
- Knowledge graph traversal
- Reflection retrieval
- Context aggregation

This component represents the implementation of ADR-0002.

---

## 3. Digital Twin

The central representation of the learner.

The Digital Twin consists of four complementary layers.

### Structured Profile

Explicit learner attributes.

Examples:

- Skills
- Goals
- Interests
- Knowledge levels
- Learning preferences

---

### Episodic Memory

Educational experiences stored as semantic memories.

Examples:

- Completed lessons
- Study sessions
- Projects
- Questions asked
- Feedback received

---

### Knowledge Graph

Structured representation of relationships.

Examples:

- Topic dependencies
- Skill hierarchies
- Course prerequisites
- Career pathways

---

### Reflection Memory

Higher-level insights generated from accumulated experiences.

Examples:

- Learning habits
- Persistent misconceptions
- Emerging interests
- Long-term strengths

---

# Reflection Engine

Responsible for transforming raw experiences into higher-level learner insights.

Functions include:

- Pattern discovery
- Memory summarization
- Learner evolution
- Knowledge synthesis

Reflection memories become part of the Digital Twin.

---

# Digital Twin Update Cycle

Every significant interaction follows the same lifecycle.

```
User Interaction
        │
        ▼
Retrieve Twin
        │
        ▼
Generate Response
        │
        ▼
Evaluate Interaction
        │
        ▼
Should Memory Be Stored?
        │
    ┌───┴────┐
    │        │
   No       Yes
    │        │
    ▼        ▼
Discard  Store Memory
              │
              ▼
     Update Structured Profile
              │
              ▼
      Trigger Reflection (if needed)
              │
              ▼
         Update Digital Twin
```

---

# Design Principles

The architecture follows several guiding principles.

### Persistent

Learner information survives across sessions.

---

### Modular

Each component has a clearly defined responsibility.

---

### Explainable

Recommendations should be traceable to learner evidence.

---

### Evolvable

The learner model continuously adapts over time.

---

### Research-Oriented

Every architectural component is motivated by published research and remains open to experimental validation.

---

# Current ADR Coverage

| ADR | Architectural Component |
|------|--------------------------|
| ADR-0001 | Multi-Layer Memory Architecture |
| ADR-0002 | Hybrid Retrieval Architecture |

Future ADRs will address:

- User Model
- Knowledge Graph
- Reflection Engine
- Recommendation Pipeline
- Agent Workflow

---

# Planned Evolution

The architecture will be refined after reviewing literature on:

- Reflexion
- MemGPT
- LongMem
- GraphRAG
- Multi-Agent Systems
- Educational Digital Twins

Future versions will incorporate experimental findings and implementation feedback while preserving traceability through Architecture Decision Records.

> **Version 0.3**
# Architectural Principles

The EduTwin framework is designed around the concept of a continuously evolving AI Digital Twin rather than a stateless conversational assistant.

The architecture follows six fundamental principles.

## 1. Single Source of Truth

The Digital Twin is the authoritative representation of the learner.

Every AI agent reads from and writes to the same Digital Twin rather than maintaining independent state.

---

## 2. Separation of Responsibilities

Each architectural component has a single well-defined responsibility.

Memory storage, retrieval, reasoning, learner modeling, and recommendation are independent modules that communicate through explicit interfaces.

---

## 3. Continuous Evolution

Every meaningful learner interaction has the potential to update the Digital Twin.

The learner model is therefore continuously refined rather than reconstructed from conversation history.

---

## 4. Explainability

Every recommendation should be traceable to evidence stored inside the Digital Twin.

Recommendations should never appear as unexplained language model outputs.

---

## 5. Modular AI

The language model is treated as a replaceable reasoning engine rather than the central architecture.

The intelligence of EduTwin resides primarily in the Digital Twin.

---

## 6. Research-Driven Design

Every architectural component exists because it addresses a research question identified during the literature review.

## current diagram

                    User
                      │
                      ▼
             AI Agent Layer
                      │
        ┌─────────────┼──────────────┐
        │             │              │
        ▼             ▼              ▼
  Study Coach   Career Mentor   Recommendation
                      │
                      ▼
          Retrieval Orchestrator
                      │
      ┌───────────────┼────────────────┐
      │               │                │
      ▼               ▼                ▼
 Structured      Memory Store    Knowledge Graph
 Student Twin      (ChromaDB)      (NetworkX)
      │               │                │
      └───────────────┼────────────────┘
                      ▼
             Context Builder
                      │
                      ▼
                 Gemini LLM
                      │
                      ▼
             Reflection Engine
                      │
                      ▼
          Digital Twin Updater
                      │
                      ▼
              Updated Student Twin

## Component Responsibilities

# Student Twin

Purpose:

Stores explicit learner state.

Owns:

profile
knowledge
skills
goals
interests
preferences
references to memories

Does NOT:

retrieve memories
call the LLM
perform reasoning

# Memory Store

Purpose:

Stores educational experiences.

Owns:

episodic memories
reflection memories
embeddings
metadata

Does NOT:

update learner profile
reason

# Knowledge Graph

Purpose:

Represents relationships.

Owns:

prerequisites
concept hierarchy
career pathways
topic dependencies

# Retrieval Orchestrator

Purpose:

Coordinates retrieval.

Owns:

query analysis
retrieval order
ranking
aggregation

Does NOT:

generate responses

# Context Builder

Purpose:

Produces one coherent context object.

Input

Student

Memories

Graph

Reflection

Output

Context


# Language Model

Purpose

Reasoning only.

No memory.

No learner state.

No persistence.

# Reflection Engine

Purpose

Transforms experiences into insights.

Examples

Completed five AI papers

↓

Strong interest in AI research

# Twin Updater

Purpose

Updates

profile
skills
knowledge
goals
reflections

after each interaction.

## Repository Mapping

src/

├── twin/
│   ├── student.py
│   ├── profile.py
│   ├── knowledge.py
│   ├── skills.py
│   ├── goals.py
│   ├── preferences.py
│   ├── reflection.py
│   └── memory_reference.py
│
├── memory/
│   ├── memory.py
│   ├── memory_store.py
│   ├── retriever.py
│   └── importance.py
│
├── graph/
│   ├── learner_graph.py
│   └── knowledge_graph.py
│
├── retrieval/
│   ├── retrieval_orchestrator.py
│   ├── context_builder.py
│   └── ranking.py
│
└── tests/

## Primary Data Flow

Every learner interaction follows the same lifecycle.

User Question

↓

Retrieve Student Twin

↓

Retrieve Memories

↓

Retrieve Knowledge Graph

↓

Build Context

↓

Language Model

↓

Generate Response

↓

Evaluate Interaction

↓

Store Memory

↓

Generate Reflection (if required)

↓

Update Student Twin