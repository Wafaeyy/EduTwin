# ADR-0003: Represent Preferences as Contextual Affinity Beliefs

**Status:** Accepted

**Date:** 14/07/2026

**Authors:** EduTwin Research Team

---

# Context

Traditional adaptive learning systems and conversational AI assistants often
represent learner preferences as deterministic values.

Example:

- Preferred explanation style = Detailed
- Preferred learning resource = Video

This representation assumes that a learner possesses one stable preference
for each dimension.

However, educational preferences are rarely deterministic.

A learner may:

- Prefer videos when learning algorithms.
- Prefer written material for mathematics.
- Prefer concise explanations when reviewing.
- Prefer detailed explanations when learning a new concept.
- Have no strong preference in some situations.

Preferences also evolve continuously through interaction.

Therefore, representing preferences as fixed values does not accurately model
human learning behaviour.

---

# Decision

EduTwin will represent preferences as **contextual belief models** rather than
deterministic attributes.

Each preference consists of:

- Preference Dimension
- Context
- Affinity Scores
- Supporting Evidence
- Last Updated

Instead of storing one preferred value, the Digital Twin stores affinity scores
for every possible option.

Example:

Preference Dimension:
Explanation Depth

Context:
Programming

Affinity Scores:

- Short: 0.18
- Medium: 0.61
- Detailed: 0.92

These scores are independent and **do not form a probability distribution**.

They represent the current strength of the Twin's belief that the learner
prefers a specific option within a given context.

---

# Why Not Probability Distributions?

Probability distributions require:

Σ P(x) = 1

Human preferences do not satisfy this constraint.

Example:

A learner may simultaneously enjoy

- Videos
- Reading
- Interactive Coding

All three can receive high affinity scores.

Therefore EduTwin models **independent affinities** instead of probabilities.

---

# Evidence-Based Updates

Preferences are never edited directly by AI agents.

Interaction flow:

User

↓

Interaction Analyzer

↓

Interaction Signals

↓

Memory Decision Node

↓

Memory Store

↓

Twin Updater

↓

Preference Belief Update

↓

Digital Twin

Only the Twin Updater may modify preference beliefs.

---

# Context Dependency

Preferences are always conditioned on context.

Example:

Programming

Explanation Depth

Short: 0.12

Medium: 0.48

Detailed: 0.90

------------------------------------

Exam Revision

Explanation Depth

Short: 0.88

Medium: 0.21

Detailed: 0.15

This allows the Twin to personalize explanations differently depending on
learning situation.

---

# Separation of Responsibilities

Memory

Stores immutable evidence.

Digital Twin

Stores current beliefs.

Twin Updater

Transforms evidence into updated beliefs.

Recommendation Engine

Consumes beliefs.

Study Coach

Consumes beliefs.

Career Mentor

Consumes beliefs.

No agent modifies beliefs directly.

---

# Benefits

- Models uncertainty.
- Models evolving learner behaviour.
- Supports explainability.
- Supports continual learning.
- Avoids hard-coded preferences.
- Better reflects real human learning behaviour.

---

# Consequences

Pros

- Flexible.
- Explainable.
- Research-oriented.
- Easy to extend.
- Context-aware.

Cons

- More complex update logic.
- Requires evidence aggregation.
- Requires Twin Updater algorithms.
- Slightly larger Twin representation.

---

# Future Work

Future research will investigate:

- Bayesian belief updates.
- Reinforcement learning based preference adaptation.
- Confidence estimation.
- Forgetting mechanisms.
- Temporal preference drift.