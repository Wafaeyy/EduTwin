# Explainability Framework

**Team Beta · Week 1, Day 1 · Step 5 Deliverable**

The rulebook for how the system justifies its decisions — to the student (trust) and to the researchers (proof). Every mechanism below is deterministic where a decision is made, and LLM-based only where language is produced.

---

## 1. The Explanation Template — five questions every justification can answer

| Question | Example (recommendation: "Review Graph Algorithms") |
|---|---|
| **Why?** | Mastery in graph algorithms has been declining |
| **Based on what evidence?** | Quiz accuracy 52% (below 55% threshold); mastery score dropped 0.71 → 0.48 over 3 weeks |
| **Which Twin attributes influenced this?** | `tracked_concepts`, `historical_accuracy_trends`, `career_goals` |
| **Confidence?** | High — two independent signals (quiz accuracy, mastery trend) agree |
| **Alternative?** | Continuing with new ML topics ranked lower: graph algorithms is a prerequisite and a stated career-goal requirement |

The template is the *maximum* rendering. How much of it becomes visible per turn is governed by the stakes rule (Section 3). The decision record (Section 2) always captures the full evidence regardless.

## 2. Two Audiences — every decision produces two renderings of the same evidence

**Decision record (always written; student never sees it).** Machine-readable audit entry:

```json
{"agent": "study_coach",
 "decision": "example-first repair of conditional probability, skipping basics",
 "evidence": ["conditional_probability = 0.45 (shaky)",
              "probability_basics = 0.80 → basics skipped",
              "recent P(A|B)/P(B|A) inversion, 4 days ago → anchored on the flip",
              "style = example-driven → scenario before formalism"],
 "confidence": 0.8}
```

Three consumers: **evaluation** (Week-8 personalization metrics are computed from these records; the two-student demonstration is proven by placing two records side by side), **debugging** (the record turns "it broke" into "this component broke on this data"), and **the user-facing layer** (visible rationales are renderings of this record — never generated from thin air).

**User rationale (visibility governed by stakes).** Human language, warm, addressed as "you", produced by `explain-v1` citing only supplied evidence.

Recorded explanation depth never scales down; visible explanation depth scales with stakes.

## 3. The Stakes Rule — who sees how much, decided deterministically

**Design decision (approved):** *button-everywhere + deterministic auto-expand list.*

- **Default (all turns):** the reply ships with a one-line rationale or a collapsed "why?" affordance. The full five-question block is always one click away. Rationale: forcing full justifications on every turn causes explanation fatigue — students stop reading justifications entirely, killing the feature's value exactly where it matters. The button lets each student set their own explanation depth implicitly, per message.
- **Auto-expand exceptions:** a short, versioned list (`stakes-list-v1`) of decision types whose evidence opens itself — the moments where a reasonable student's reaction is *prove it*, and where a stressed student cannot be relied on to click:

```python
AUTO_EXPAND = {
    ("predictor", "risk_level=high"),        # "you are at risk of failing"
    ("mentor",    "direction_change"),       # "spend this month on X instead"
}
# default for any pair not listed: routine (button only)
```

**Why a lookup and not an LLM judgment:** the list is keyed on fields the agents' structured outputs *already carry* (`risk_level` is computed by the Prediction Engine's thresholded math; `direction_change` is a field of the Mentor's report). No component ever judges its own importance; LLM importance-scores are uncalibrated (the same reply can score 78 one run and 85 the next), which would make the safety feature nondeterministic at the threshold. Rules that can be written down in advance are checked in code.

**The list learns from data, not vibes:** every "why?" click is logged. Reply types that students consistently expand are candidates for promotion to the auto-expand list in the next version. Click logs are also a free Week-8 signal (which decisions do students demand proof for?).

## 4. Research Position — evidence, not chain-of-thought

Explanations are **reconstructed from observables** — the inputs an agent received (its Twin slice, its briefing) and the output it produced — never transcribed from model introspection. Asking an LLM to narrate its own reasoning yields unreliable self-reports; the auditor therefore watches the facts and never interviews the suspect.

Structural guarantee: the Explainability Agent is **independent by construction** — it reads all agents' inputs and outputs, decides nothing, writes nothing to the Twin (audit log only). If each agent explained itself, the component that made the decision would author the story of why the decision was good. An external observer with no stake in the decision produces explanations that are evidence, not marketing. (ADR: *why explanations expose evidence rather than hidden reasoning.*)

## 5. The Verification Gate — `flag: evidence_insufficient`

`explain-v1` rule 5: if the supplied evidence cannot ground the decision, the rewriter outputs exactly `flag: evidence_insufficient` and nothing else. The explanation layer thereby doubles as an always-on QA gate over the entire pipeline: a Coach reply that ignored its briefing, a mis-scored ranking, or a wrong retrieved slice gets caught at the last stage before the student.

### Flag-handling policy (approved)

```
flag fires
  → RETRY ONCE (re-run the producing agent on the same inputs; LLM sampling
     variance may resolve it; a deterministic agent will not change — its
     flag indicates a bug, so retry only re-runs the rewriter)
  → still flagged → HONEST DEGRADE, by agent:
       coach turn        → safe generic tutoring move ("let me approach this
                            differently — tell me what you know about X?")
       recommendation    → enter the fallback ladder AT RUNG 2 (see 5.1)
       high-risk / consequential claims → HARD VETO: an unjustifiable
                            "you might fail" must never ship. The heavier
                            the claim, the stricter the evidence requirement
                            — the gate and the stakes rule compose.
  → ALWAYS: log the event
```

```json
{"event": "evidence_insufficient", "agent": "recommender",
 "decision": {...}, "evidence": [...], "turn": "sess_881/7",
 "resolution": "retry_failed -> fallback_rung2"}
```

Log consumers: debugging (which agent produced ungroundable output on which data), evaluation (groundability rate per agent — a publishable table), audit trail (a system that records its own unjustifiable moments is the trust story itself).

**Honest caveat:** the rewriter is an LLM; the gate has false alarms and misses. It is a smoke alarm, not a judge — cheap, always-on, audited by Week-8 human spot-checks.

### 5.1 The Fallback Ladder (recommendation degrade path)

Two distinct entrances — the distinction matters:

| Trigger | Meaning | Entry rung | Log event → responder |
|---|---|---|---|
| **Empty shelf** (topic valid, corpus has < K items) | Healthy scorer, nothing to score | **Rung 1** | `coverage_gap` → ingestion pipeline stocks the topic (gap-triggered fetch) |
| **Flag-veto** (items existed, ranking unjustifiable, retry failed) | Scorer itself suspect | **Rung 2** — skip rung 1: re-ranking neighbor shelves runs the same possibly-broken scorer on different items | `evidence_insufficient` → developer debugs the scorer |

The rungs:

1. **Graph neighbors** — offer well-stocked prerequisite/adjacent topics from the knowledge graph, *labeled honestly* ("no Bayesian-networks materials yet — these conditional-probability resources cover its foundation").
2. **Coach handoff** — the router wakes the Study Coach: "let's work through it together right now." A different component on a different code path; a scorer bug cannot follow. Often the better outcome regardless.
3. **Honest empty** — "nothing suitable in the catalog for this yet." An honest empty beats a padded list: every padded list teaches the student to distrust all future rankings.

**Forbidden rung:** never fall back to LLM-generated resources at request time. The empty shelf is when hallucination temptation peaks; the corpus rule is hardest exactly there.

**Loop-closer:** every rung-1 entry also logs the coverage gap, prioritizing the topic in the next ingestion run — *teach now, stock tonight, remember in between* (the Coach's `interaction_signal` from the rung-2 session personalizes the next day's freshly stocked ranking).

## 6. Assembly — how the pieces run per turn

```
agent output + its evidence (Twin slice / scoring factors / risk factors)
        ↓
stakes lookup (Section 3)  → routine | consequential          [code]
        ↓
explain-v1 (Sections 1, 4) → grounded rationale + record,
                              or flag                          [LLM]
        ↓
flag? → retry → degrade/veto per Section 5                    [code]
        ↓
ALWAYS: decision record → audit log                            [code]
routine: one-liner + "why?" button   |   consequential: full block
```

> **Versioned artifacts introduced by this framework:** `stakes-list-v1` (auto-expand entries), `explain-v1` (rewriter prompt, defined in Prompt Architecture). Changes increment versions; evaluation results are reported against them.

> **Cross-references:** rewriter template and rules — `Prompt_Architecture.md` §6. Decision-record consumers and the two-audience design — `Agent_Ecosystem.md` (Explainability Agent). Pipeline position (Stage 8, always runs, never routed to) — `Personalization_Pipeline.md`.
