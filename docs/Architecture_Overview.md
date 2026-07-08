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