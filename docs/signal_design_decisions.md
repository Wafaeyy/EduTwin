# Signal Design Decisions — Study Coach

Record of decisions made about the signal vocabulary, and why. Written so the
reasoning is not lost. Nothing here is applied to the prompt yet — see
"Pending edits" at the bottom for what still needs doing and in what order.

---

## 1. New signal: `mastery_unstable`

### The problem it solves

A student answers two questions correctly, then gets one wrong on the same
concept. The current vocabulary has no word for this.

- `misconception_detected` means the student holds a **wrong belief**. That is
  too strong. Two correct answers show they do not hold a wrong belief.
- `mastery_evidence` alone hides the failure.
- Emitting both produces two contradictory claims about the same concept, and
  leaves the Twin to work out that they conflict.

The Coach is the component that actually watched the session. It should report
one coherent observation instead of two claims that fight.

### Meaning

> The student both applied a concept correctly AND got it wrong, in the same
> session.

### Trigger rule

Use `mastery_unstable` when the student, in the same session, both applies a
concept correctly **and** either:

- states a wrong answer for that concept, or
- offers **two competing answers without choosing between them**.

Do **not** use it for simple hesitation, thinking aloud, or a self-correction
that lands on the right answer.

### It replaces, not accompanies

When `mastery_unstable` applies, emit it **instead of** the separate
`mastery_evidence` and `misconception_detected` signals for that concept. One
coherent claim, not two contradictory ones.

### What the Twin should do with it

Do not move the belief much, and probe this concept deliberately in a future
session. No other signal produces that action.

---

## 2. How hesitation is handled

Decision: hesitation that ends in a **correct** answer stays as
`mastery_evidence` with lowered confidence. It does not become
`mastery_unstable`.

Reason: if `mastery_unstable` fires on both right and wrong answers, the Twin
cannot tell the two cases apart and the label loses meaning. Keep it meaning one
crisp thing — **the student actually got it wrong at some point this session**.

| What happened | Signal | Confidence |
|---|---|---|
| Right, no hesitation | `mastery_evidence` | normal band |
| Right, but hesitated first | `mastery_evidence` | lower end of band + note in `detail` |
| Right earlier, then two competing answers | `mastery_unstable` | 0.4 – 0.5 |
| Right earlier, then a committed wrong answer | `mastery_unstable` | 0.6 – 0.7 |

### Why the two-competing-answers case scores lower

One of the two answers the student offered is correct. They are partly there —
closer than a student who states one wrong answer firmly. So the Coach is **less
sure** how deep the problem goes.

Note this is not "the mistake was milder, so lower the number." Confidence
measures **certainty about the claim**, never **severity of the mistake**.
Severity belongs in `detail` (see §4).

---

## 3. Missing rule: confidence should be able to go DOWN

The current confidence anchors only describe what makes confidence go **up**
(more instances, more explanation). Nothing describes what lowers it.

Rule to add:

> Lower the confidence within a band when evidence in the same session points the
> other way. A student who reaches the right answer only after considering a
> wrong one shows weaker mastery than one who answers directly. Note the
> hesitation in `detail`.

This also covers the reverse case: a student who fails **after** two successes is
weaker evidence of a misconception than one who fails cold.

---

## 4. What goes in `detail`

`detail` carries the things `confidence` must not:

- **Severity.** "Student self-corrected mid-answer; did not commit to a wrong
  answer" vs. "Student stated a wrong answer with no hesitation."
- **The tally.** "Correct on 2 of 3 attempts this session." Lets the Twin set its
  own threshold instead of trusting the Coach's label.
- **The specific fork.** "Student offered 2cos(x²) or cos(x²) without choosing"
  is far more useful than "student was unsure."

---

## 5. Open question — the `briefing_contradicted` visibility rule

The current rule says report a conflict "every turn the conflict is visible."
The word *visible* is undefined, and in testing the model decided for itself when
a conflict had stopped being visible.

A proposed fix — "a conflict is visible whenever what you observe differs from
the record in either direction" — was **rejected**: once a contradiction fires on
turn 1, that condition stays true forever, so the signal would fire on every
later turn regardless of what the student does. A stuck bit, not a fix.

**Likely real cause:** the tension is an artifact of the coarse concept label.
Under a split label it disappears:

- `chain_rule_linear` → student competent, record says 0.20 → genuinely contradicted
- `chain_rule_composite` → student wobbling, record says weak → consistent, no conflict

Both signals are cleanly true about different nodes. **Run Scenario G before
touching this rule** — granularity may resolve it without any prompt change.

---

## 6. Not the Coach's job (Twin-side)

- **Supersession / deduplication.** The Coach cannot know what the Twin stores or
  what it emitted in earlier sessions. See the interface report, Case E.
- **Resolving contradictory signals across sessions.** The Coach reports
  instability *within* a session; the Twin handles inconsistency *across*
  sessions, because only it sees history.

---

## Pending edits — in this order

**Do not edit the prompt before running Scenarios E, F, and G.** Two of those
scenarios are diagnostics whose results decide what the edit should be.

1. **Run E, F, G against v2 unchanged.** Baseline on untested branches.
2. **Then apply:**
   - `mastery_unstable` added to the enum, with the trigger rule from §1
   - the replaces-not-accompanies rule from §1
   - the confidence-goes-down rule from §3
   - the `detail` guidance from §4
   - concept keys: *"reuse a key from the briefing's concept mastery list when
     one applies; only invent a label when nothing fits"* (locks in behaviour
     observed in Scenarios A and B, which currently happens by luck)
   - step 3 rewording — **only if Scenario F shows it is still skipped at 0.10**
   - the visibility rule — **only if Scenario G shows granularity does not
     resolve it**
3. **Re-run E and G** to confirm the edits did what was expected.

One thing to watch after adding `mastery_unstable`: the model will probably
over-apply it. Any small hiccup will become "unstable." Check that the strict
trigger in §1 holds.