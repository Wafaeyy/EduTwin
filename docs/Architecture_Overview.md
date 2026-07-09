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