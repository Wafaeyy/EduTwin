# Coach → Twin Interface: Signal Contract and Open Questions

**From:** Researcher (Agent / Prompt Architecture lane)
**To:** Digital Twin team
**Status:** Coach agent is running end-to-end against a mock Twin. This document
defines what the Coach will emit, what it deliberately will *not* do, and the
decisions the Twin side needs to make before the interface is frozen.

---

## 1. Why this document exists

The Study Coach is live and emitting structured `interaction_signal` blocks on
every turn. Those signals are the **only** channel through which anything
learned during a tutoring session reaches the Twin.

The Coach was deliberately built to be *narrow*: it observes and reports, and it
does not aggregate, deduplicate, or update anything. That means a set of
decisions now sits unambiguously on the Twin side. This document lists them so
they get made explicitly rather than discovered during integration.

---

## 2. What the Coach emits

Appended to the Coach's natural-language reply, **when and only when** that turn
produced diagnostic evidence:

```
<signal>
{
  "concept":    "chain_rule",
  "signal":     "gap_confirmed | misconception_detected | mastery_evidence |
                 confusion_resolved | briefing_contradicted",
  "detail":     "<one sentence>",
  "evidence":   "<quote or paraphrase of what the student said or did>",
  "confidence": 0.0-1.0
}
</signal>
```

### Guarantees the Coach makes

1. **Per-turn emission.** A signal is emitted on the turn the evidence appeared.
   The Coach never withholds a signal in anticipation of later turns.
2. **Observed evidence only.** The `evidence` field always cites what the student
   said or did in the current session. The briefing is **never** cited as
   evidence. If the only support for a claim is the briefing itself, no signal is
   emitted.
3. **Session-local confidence.** `confidence` describes the strength of *this
   session's* observation in isolation. It is not inflated by history the
   briefing reports.
4. **Contradiction is reported, not resolved.** When live behaviour conflicts
   with the briefing, the Coach emits `briefing_contradicted` and responds to
   what it observed. It does not attempt to decide which is correct.

### Guarantees the Coach does *not* make

- It does not deduplicate. Three turns of evidence about one concept produce
  three signals.
- It does not aggregate across sessions. It has no memory between sessions.
- It does not know when a session ends (see §4).

---

## 3. Confidence calibration (and a warning)

The Coach scores confidence against fixed, checkable anchors:

| Range | Condition |
|---|---|
| 0.3 – 0.4 | Correct answer, no reasoning shown |
| 0.5 – 0.7 | Student explains the mechanism in their own words, once |
| 0.8 – 0.9 | Correct application to two or more distinct problems *within this session* |
| > 0.9 | Not used |

**Warning for the Twin side:** these are LLM self-reported numbers, and LLMs are
known to be poorly calibrated and to skew high. In observed testing the model
returned 0.85 for a case the anchors placed at 0.5–0.7.

Treat `confidence` as a **coarse ordinal signal** (weak / moderate / strong), not
as a probability. If a Twin update threshold depends on a specific numeric cutoff,
that threshold should have a safety margin or a hard cap applied downstream.

---

## 4. Why signals are per-turn, not per-session

An earlier design considered emitting one summary signal at session end. It was
rejected as unimplementable:

- **The Coach cannot detect session end.** It sees the history so far and the
  current message. It has no lookahead and cannot distinguish "turn 3 of 3" from
  "turn 3 of 10."
- **The application cannot detect it reliably either.** Explicit "end session"
  clicks are rare; tab closes may never reach the backend; inactivity timeouts
  fire late; crashes fire never.
- **Conversation history is process memory.** It is discarded when the session
  ends. Anything not already emitted as a signal is lost with it.

**Consequence:** per-turn emission is what makes the pipeline robust to sessions
ending messily — which is the normal case. Every turn banks its own evidence.

---

## 5. The four cases the Twin must handle

### Case A — Corroboration (multiple signals, same concept, same direction)

Three signals of `mastery_evidence` on `chain_rule`, confidences 0.6 / 0.6 / 0.7.

Two naive strategies both fail:

- *Overwrite with latest* → the Twin has amnesia; three observations collapse to one.
- *Average* → three 0.6s average to 0.6; repetition adds nothing, which is wrong.

What is needed is **accumulation with diminishing returns** — each corroborating
observation moves the belief toward certainty by less than the last. Conceptually
Bayesian: each signal is evidence updating a prior, not a replacement value.

### Case B — Contradiction (`briefing_contradicted`)

The Twin holds a misconception flag; the student demonstrates correct reasoning.
The Coach reports the conflict and does not resolve it.

Open: how much evidence retires a stored belief? A single contradicting
observation is weak (could be recall, luck, or copying a worked example).
Retiring on one signal makes the Twin twitchy; requiring too many makes it stale.

Recommendation to consider: **retire to a `resolved_misconceptions` history with a
timestamp rather than hard-deleting.** A misconception that resurfaces later is
important data.

### Case C — Cross-session repetition

Student answers correctly, closes the app. Next day, correct again. Day after,
correct again. Each session is one turn, so each signal is honestly ~0.6 — they
never individually escalate.

This is **not** a problem with the Coach; it is the accumulation working as
intended. Note that three correct answers on three separate days is *stronger*
evidence than three in one sitting: within a session the student is primed and
may be pattern-matching their own previous answer, whereas across days each
answer independently survives the forgetting interval (spacing effect).

A well-designed aggregator should therefore produce a **higher** final belief for
the spaced case than for the compressed one.

### Case D — Conflicting signals over time

Turn 5 says mastery; turn 20 says misconception. Recency should win partly — but
the conflict is itself information: it says the belief is unstable. A sensible
response is to lower *confidence in the belief* and flag the concept for a
deliberate probe, rather than silently flip-flopping.

---

## 6. Two hazards to design against

**Double-counting.** The Coach's confidence must not be inflated by history the
briefing reports, and the Twin must not re-count evidence it already holds. If
the briefing says "answered correctly twice before," the Twin already owns those
two observations. Counting them again on the third turn would weigh the same
evidence twice.

**Thrashing.** If re-flagging a retired misconception is as easy as retiring it,
the Twin oscillates on noisy evidence. Some hysteresis (asymmetric thresholds)
is usually needed.

---

## 7. Questions for the Twin team

### Storage model — the blocking question

1. Does the Twin store a **timestamped log of signals**, or only current field
   values that get overwritten? *(If it is the latter, none of §5 is possible and
   the `confidence` field is decorative. This is the single decision that most
   constrains everything else.)*
2. Are signals stored as **proposals** the Twin reasons over, or applied as
   **direct writes** to Twin fields? Who owns the write?
3. Is there an audit/decision record when a belief changes — what changed, when,
   and citing which signals?

### Aggregation

4. What is the aggregation rule for repeated same-direction signals (Case A)?
5. How many corroborating signals, at what confidence, retire a stored
   misconception (Case B)?
6. Is the aggregation symmetric, or is re-flagging harder than retiring
   (hysteresis)?
7. Is there time decay on old signals? Over what horizon?
8. Does the Twin distinguish signals from *different sessions* vs. the same
   session (Case C)? If not, spaced evidence and massed evidence are treated
   identically.

### Confidence

9. Does any Twin threshold depend on the numeric `confidence` value? If so, is
   there a cap or margin applied, given §3?
10. Should the Twin store its own belief-confidence separately from incoming
    signal-confidence? *(Recommended: they answer different questions — "how
    strong is this observation" vs. "how sure am I about this student.")*

### Retrieval boundary — needed for the Week-8 experiment

11. Does retrieval return **records** (objects for the Coach side to render into
    a briefing) or **pre-formatted text**?
    *This determines where the A/B/C experimental variable lives.* The experiment
    holds retrieval constant and varies only briefing phrasing; if retrieval
    returns text, the variable sits in Twin-team code and the experiment cannot
    be run cleanly from the agent side.
12. What is the Coach's privilege scope — exactly which fields are returned? Per
    the Ecosystem design the Coach receives a least-privilege slice and
    explicitly **not** career goals. Is that enforced in retrieval?
13. What is the concrete schema of a returned record? The Coach currently mocks:
    `learning_style`, `concept_mastery` (concept → 0-1), `recent_errors` (list),
    `known_misconceptions` (list).

### Schema agreement

14. Is `concept` a free-text string or drawn from a controlled vocabulary /
    concept graph? *(Free text will fragment: "chain_rule" vs "chain rule" vs
    "Chain Rule" become three concepts.)*
15. Is the signal enum agreed? Currently: `gap_confirmed`,
    `misconception_detected`, `mastery_evidence`, `confusion_resolved`,
    `briefing_contradicted`.
16. Should signals carry a `session_id` and `turn_index`? *(Needed to answer
    Q8 and to detect within-session duplicates.)*

---

## 8. Summary of the division of responsibility

| | Coach | Twin |
|---|---|---|
| Scope | One turn | All history |
| Question answered | "How strong is *this observation*?" | "What do I believe about *this student*?" |
| Memory | None (stateless per call) | Persistent |
| On contradiction | Reports it | Resolves it |
| On repetition | Emits each time | Aggregates |

The line to hold: **the Coach reports what it saw; the Twin decides what to
believe.**