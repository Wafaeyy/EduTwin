# Digital Twin Ontology

**Project:** EduTwin – AI Digital Twin Framework for Personalized Education

---

# Purpose

This document defines the semantic concepts used throughout the EduTwin architecture.

Its purpose is to establish a shared vocabulary across all research, implementation, and future publications.

Every component of the Digital Twin must conform to these definitions.

This ontology acts as the semantic contract between:

- Twin Models
- Twin Updater
- Memory System
- Study Coach
- Career Mentor
- Recommendation Engine
- Prediction Module
- Explainability Module

---

# Core Principle

The Digital Twin does not attempt to remember conversations.

Instead, it maintains an evolving semantic representation of the learner.

Raw interactions are transformed into structured memories.

Structured memories are transformed into updated beliefs.

These beliefs collectively form the Digital Twin.

---

# High-Level Architecture

```
                 User
                  │
                  ▼
        Conversation / Interaction
                  │
                  ▼
        Interaction Analyzer
                  │
                  ▼
        Interaction Signals
                  │
                  ▼
         Memory Decision Node
                  │
                  ▼
          Episodic Memory Store
                  │
                  ▼
            Twin Updater
                  │
                  ▼
        Student Digital Twin
                  │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
 Study Coach   Recommendation   Career Mentor
```

---

# Digital Twin Components

The Student Twin is composed of multiple semantic models.

Each model represents a different aspect of the learner.

No model should duplicate information contained elsewhere.

---

# 1. Profile

## Definition

Represents the stable identity of the learner.

Profile contains information that changes rarely.

## Stores

- Student ID
- Name
- University
- Field of Study
- Academic Year

## Does NOT Store

- Goals
- Knowledge
- Skills
- Preferences
- Memories
- Performance

## Updated By

User only.

## Used By

All modules.

---

# 2. Goals

## Definition

Represents educational objectives the learner wishes to achieve.

Goals define optimization targets for personalization.

## Stores

- Goal title
- Description
- Priority
- Status
- Progress
- Target completion date

## Does NOT Store

- History of changes
- Performance
- Learning evidence

Historical changes belong to Memory.

## Updated By

Twin Updater.

## Used By

- Study Coach
- Recommendation Engine
- Career Mentor
- Prediction Module

---

# 3. Preferences

## Definition

Represents contextual beliefs about how the learner prefers to learn.

Preferences are **not deterministic**.

They are affinity belief vectors conditioned on learning context.

## Stores

- Preference Dimension
- Learning Context
- Belief Vector
- Last Updated

Example

Explanation Depth

Programming Context

Short → 0.20

Medium → 0.61

Detailed → 0.92

## Does NOT Store

- Raw interaction evidence
- Conversations

Evidence belongs to Memory.

## Updated By

Twin Updater only.

## Used By

- Study Coach
- Recommendation Engine
- Explainability

---

# 4. Knowledge

## Definition

Represents what the learner currently understands.

Knowledge models cognitive understanding rather than practical ability.

Knowledge is represented as interconnected concepts.

Each concept maintains a continuously updated mastery estimate.

## Stores

- Concept
- Mastery
- Confidence
- Prerequisites

## Does NOT Store

- Practice performance
- Coding ability

Those belong to Skills.

## Updated By

Twin Updater.

## Used By

- Recommendation Engine
- Prediction Module
- Study Coach

---

# 5. Skills

## Definition

Represents the learner's practical ability to perform tasks.

Skills describe demonstrated competence rather than conceptual understanding.

## Stores

- Skill
- Proficiency
- Confidence
- Related Knowledge

## Does NOT Store

- Learning preferences
- Goals
- Memories

## Updated By

Twin Updater.

## Used By

- Career Mentor
- Recommendation Engine
- Prediction Module

---

# 6. Interests

## Definition

Represents subjects that naturally attract the learner.

Interests influence engagement rather than competency.

Interests may evolve over time.

## Stores

- Interest
- Affinity
- Confidence

## Updated By

Twin Updater.

## Used By

- Recommendation Engine
- Career Mentor

---

# 7. Memory

## Definition

Represents immutable evidence collected from learner interactions.

Memory never stores beliefs.

Memory stores observations.

## Stores

Examples

- Solved recursion problem
- Asked for deeper explanation
- Completed quiz
- Failed exercise
- Changed career goal

## Does NOT Store

- Mastery
- Preferences
- Goals

Those belong to the Twin.

## Updated By

Memory Decision Node.

## Used By

Twin Updater.

---

# 8. Student Twin

## Definition

Represents the current semantic state of the learner.

The Student Twin is an aggregation of all learner models.

## Contains

- Profile
- Goals
- Preferences
- Knowledge
- Skills
- Interests

The Twin itself contains no AI logic.

It is purely a structured representation.

---

# Component Responsibilities

| Component | Responsibility |
|------------|---------------|
| Interaction Analyzer | Convert conversations into structured interaction signals |
| Memory Decision Node | Decide whether signals should become memories |
| Memory Store | Store immutable episodic evidence |
| Twin Updater | Update learner beliefs using memories |
| Study Coach | Generate personalized educational guidance |
| Career Mentor | Generate career recommendations |
| Recommendation Engine | Recommend learning resources |
| Prediction Module | Estimate future outcomes |
| Explainability Module | Explain recommendations and Twin updates |

---

# Update Permissions

| Component | Read Twin | Write Twin |
|-----------|-----------|------------|
| User | ❌ | Indirectly |
| Study Coach | ✅ | ❌ |
| Career Mentor | ✅ | ❌ |
| Recommendation Engine | ✅ | ❌ |
| Prediction Module | ✅ | ❌ |
| Explainability Module | ✅ | ❌ |
| Memory Decision Node | ✅ | ❌ |
| Twin Updater | ✅ | ✅ |

The Twin Updater is the **only component** permitted to modify the Digital Twin.

---

# Information Flow

```
Conversation

↓

Interaction Analyzer

↓

Interaction Signals

↓

Memory Decision Node

↓

Memory

↓

Twin Updater

↓

Digital Twin

↓

AI Agents
```

No AI agent writes directly to the Twin.

---

# Research Principles

1. The Twin stores beliefs, not conversations.

2. Memory stores evidence, not beliefs.

3. Every Twin update must be explainable through supporting memories.

4. Every AI agent is read-only with respect to the Twin.

5. The Twin evolves continuously as new evidence is collected.

6. Semantic concepts are represented independently to avoid duplication and maintain modularity.

---

# Future Extensions

Future versions of EduTwin may include:

- Knowledge Graph reasoning
- Bayesian belief updates
- Temporal decay and forgetting
- Social learning models
- Cognitive state estimation
- Affective state modeling
- Multi-modal interaction signals
- Longitudinal learning analytics