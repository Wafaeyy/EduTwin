# Team Beta — Resource Recommendation Engine

**Complete project context and technical handover.**

This document describes everything built, decided, and still open for the
Recommendation Engine component of the EduTwin multi-agent educational system.
It is written to be handed to another AI assistant or teammate as complete
context, or kept as a personal reference.

> **If you read nothing else, read Section 14.** There is one integration
> problem — a missing `twin_id` — that currently makes the entire learner
> memory system inert in the live system. It is not a code bug and cannot be
> fixed from inside this component.

---

## 1. Who is building this, and how they learn

**Builder:** a Computer Engineering student, working as a researcher in an
8-week AI research internship, part of Team Beta.

**Python knowledge:** near-zero at the start of this project. Learned Python
fundamentals (variables, functions, dictionaries, lists, loops, conditionals,
classes, modules/packages, `try`/`except`, regex, JSON, SQL, threading,
hashing) progressively, alongside building this real system — not through toy
examples.

**How this person needs to be taught, if you are continuing this work:**

- Explain every new concept from zero, assuming no prior Python background, in
  very simple, beginner-friendly language.
- After every step, provide the **whole current file's code** (not just a
  diff or snippet) and say exactly which file path to put it in. Giving a
  fragment with "add this below function X" has repeatedly caused the change
  to be missed entirely — the extraction-cache functions were lost this way
  and only surfaced later as an `ImportError`.
- Explain code line by line, in simple terms.
- Give direct, honest feedback — including admitting bugs and fixing them
  transparently. Several real bugs were found this way; see Section 11.
- Prefer concrete worked examples over abstract explanations.
- Move at a deliberate pace: one component at a time, tested before moving on.
- **Explain the "why" before the "what."** Handing over a file without first
  explaining what problem it solves does not work — this was tried and had to
  be redone.
- **Never present a guess as a fact.** When something cannot be determined
  without seeing the actual output, say so and ask for it.

This person is not on Team Alpha (who build the Digital Twin) and is not the
Orchestrator builder (a teammate owns that) — this person owns the
Recommendation Engine specifically.

---

## 2. The project

### Research question

> How should AI agents consume a continuously evolving Digital Twin to produce
> personalized, explainable, and adaptive educational guidance that outperforms
> a traditional stateless LLM assistant?

**Core thesis:** personalization should be an architectural property of the AI
system, not merely a prompt-engineering trick.

### System context

- **Team Alpha** owns the Digital Twin, a Memory System, and a knowledge graph.
- **Team Beta** designs the AI reasoning architecture that consumes the Digital
  Twin — multi-agent architecture, context engineering, recommendation systems,
  explainability, adaptive personalization.
- **This component:** the Resource Recommendation Engine — recommends
  educational resources (videos, playlists, books, courses, articles,
  tutorials, documentation, research papers, practice platforms) that are
  genuinely useful, verified, accessible, and personalized.
- **A teammate** is building the Orchestrator, which routes learner requests to
  the right agent and supplies this engine with a prose briefing plus the
  learner's message.

### Core architectural principle (non-negotiable)

**LLMs must NOT make the final recommendation decision.**

LLMs are used only for:

- understanding natural-language requests (the Orchestrator),
- extracting structured fields from prose (context and request extractors),
- understanding unstructured resource content (transcripts, article text),
- generating natural-language explanations (a separate agent).

All filtering, scoring, ranking, and the final recommendation decision are
**100% deterministic code** — reproducible, explainable, debuggable.

**Where this principle proved its value:** a bug was found where every
discovered resource claimed to be a video and collected 30 unearned scoring
points. Because scoring is transparent arithmetic with a printed breakdown, a
resource showing `format 30` beside a GeeksforGeeks category-listing URL was
obviously wrong. An LLM-scored system would have produced a confident,
plausible, equally incorrect answer with nothing to inspect.

---

## 3. How the engine demonstrates the research question

The clearest demonstration is the learner history system:

| | Stateless LLM assistant | This engine |
|---|---|---|
| Learner asks twice | May give different answers randomly | Identical answer, by design |
| "Recommend something else" | Often repeats itself | Excludes everything shown; searches with varied queries for genuinely new material |
| Learner rejects a resource | Forgotten immediately | Permanently excluded, across sessions, stored in Postgres |
| Learner asks why | Post-hoc rationalization | Exact score breakdown: `format 30 \| level 30 \| duration 0 \| goal 20` |

Reproducibility is deliberate. Same learner + same question = same answer, so
a recommendation can always be explained and audited. Variety is available but
must be explicitly requested via `exclude_seen`.

**Caveat, stated honestly:** history requires a `twin_id`, and the live
briefing does not currently supply one. See Section 14.

---

## 4. The pipeline, end to end

A single call runs all of this:

```
Two strings arrive: the briefing, and the learner's message
  ↓ extract learner state from the briefing   (cache → Gemini)
  ↓ extract the request from the message      (cache → Gemini → keywords)
  ↓ APPLY REQUEST: the request wins, memory fills the gaps
  ↓ normalize (field aliases, reject invalid values)
  ↓ load this learner's history from Postgres
  ↓ build search requirement (topic, level, format)
  ↓
  ├─ TIER 1: exact topic + exact level          ┐
  ├─ TIER 2: exact topic, any level             │ each filtered against
  ├─ TIER 3: semantic (neural embeddings)       │ history; stops at the
  ├─ TIER 4: entire catalog — ONLY if no topic  │ first tier that yields
  └─ TIER 5: external internet discovery        ┘ unseen resources
        ├─ query variation (8 templates, neutral first)
        ├─ analyze (infer difficulty and format)
        ├─ verify (structure → blocklist → homepage → parallel HTTP)
        └─ save all verified to Postgres
  ↓ score every resource (format 30 / level 30 / duration 20 / goal 20)
  ↓ TOPIC GATE: off-topic resources score 0 regardless of other matches
  ↓ rank by score
  ↓ drop anything below 50 (unless nothing clears it)
  ↓ cap at 5, or at the number the learner asked for
  ↓ record what was shown
  ↓ deep content analysis of the TOP resource only (cached, shared)
  ↓ format as readable text
```

---

## 5. Request handling — the request wins, memory fills the gaps

This is the most recently added behaviour and the one most likely to be
misunderstood, so it gets its own section.

**The problem it solves.** A learner's *goal* is long-term ("become a machine
learning engineer"). Their *request* is immediate ("show me videos about
calculus"). The engine originally read only the goal, so a learner asking for
calculus received machine learning resources.

**The rule:**

| Field | Taken from the request if stated | Otherwise from the Twin |
|---|---|---|
| topic | ✓ | ✓ |
| format | ✓ | ✓ |
| level | ✓ | ✓ |
| duration | ✓ | ✓ |
| count | ✓ | defaults to 5 |

So `"recommend videos about calculus"` searches calculus at the learner's
stored level and duration. `"recommend something"` uses the stored goal
entirely. When the request overrides the goal, the response says so:

> *Searching for 'calculus' as requested, rather than the stored goal 'machine learning'.*

**Implemented in** `twin/request_extractor.py` (extraction) and
`apply_request()` in `main.py` (the overlay).

### Three extraction layers

`extract_request()` tries each in turn:

1. **Cache** — this exact message was read before. Free, instant, and immune
   to Gemini being unavailable.
2. **Gemini** — full understanding. Handles any phrasing and any language,
   expands abbreviations (`calc` → `calculus`, `ml` → `machine learning`),
   leaves proper nouns alone.
3. **Keyword matching** — deterministic pattern matching. Cruder, but far
   better than nothing.

Layer 3 exists because Gemini failed repeatedly in real use — 429 (quota
exhausted), 503 (overloaded), and an unset API key. With no extraction at all,
`learner_state` is empty and **every recommendation scores 0/100**.

Keyword results are deliberately **not cached**, so a crude answer is never
reused in place of the better one once the API recovers.

### Count

`"give me 10 videos about python"` returns up to 10 rather than the default 5.
Clamped to 1–20, so `"give me 500 videos"` becomes 20 and cannot trigger
hundreds of network verifications.

Asking for 10 does not guarantee 10. Only resources passing the topic gate and
the score floor are returned; padding with weak matches would defeat the
filter. The response says so:

> *Only 6 strong matches were found, fewer than the 10 requested.*

---

## 6. Component reference

### 6.1 Learner state

**`twin/mock_twin.py`** — `normalize_learner_state()` is the adapter layer: it
maps field aliases (`current_skill_level` → `level`), rejects values outside
the known lists, and returns a clean predictable shape.

**`config.py`** — the single source of truth for `KNOWN_LEVELS`,
`KNOWN_FORMATS`, `KNOWN_DURATIONS`, and `FIELD_ALIASES`.

**`twin/context_extractor.py`** — the Orchestrator's `ContextBuilder` produces
a **prose string** written for LLM agents, not a structured dict. This module
makes a guarded Gemini call to extract the five fields the engine needs.

Truncation at 20,000 characters is safe because `ContextBuilder` emits
`STUDENT PROFILE & TWIN` first, always (the section order is hardcoded in
their file). Truncation loses memories and graph knowledge, never the profile.

**When the Twin holds several goals**, the prompt instructs the model to pick
the one presented as current or most recent. That selection is an LLM judgment
and is not deterministic — see Section 12.

**`twin/request_extractor.py`** — described in Section 5.

Both extractors are guarded identically: the prompt injects the actual
`KNOWN_*` constants so it cannot drift from `config.py`; the model is told to
return `null` rather than guess; only expected keys are kept; every value is
re-checked against the known lists; and every failure path degrades rather
than breaking.

### 6.2 Retrieval

**`retrieval/retriever.py`** — the five-tier ladder plus `discover_and_store()`.
Every tier is filtered against learner history via `exclude_seen()`.

**Tier 4 only runs when no topic was specified.** A catch-all is right when the
engine has no idea what the learner wants; it is wrong when they named a
topic. A real run returned all 47 machine learning resources to a learner
asking for calculus, because tier 4 matched everything and tier 5 therefore
never ran.

**`retrieval/semantic.py`** — bag-of-words vectors with cosine similarity,
built from first principles. Automatic fallback.

**`retrieval/embeddings.py`** — real neural embeddings via
`sentence-transformers` (`all-MiniLM-L6-v2`), running locally. Tried first at
startup; falls back to bag-of-words if the model cannot load.

**`retrieval/discover.py`** — real internet search via `ddgs` (DuckDuckGo).

*Query variation.* Eight fixed templates, tried in order, stopping as soon as
enough new candidates are found:

```
1.  {topic} {level} {format}
2.  {topic} {format}
3.  best {topic} {format}
4.  {topic} explained {format}
5.  how to {topic} {format}
6.  {topic} full guide {format}
7.  learn {topic} from scratch {format}
8.  {topic} crash course {format}
```

**Neutral phrasings come first, deliberately.** The original list opened with
learning-oriented templates, which produced *"learn messi from scratch video"*
for a non-academic topic — unnatural phrasing that searches badly. Templates
1–4 work for any subject; 5–8 are the academic escalation, used only when the
plain searches run dry.

In the normal case only template 1 runs, so the mechanism costs nothing until
needed. Because the list is fixed and ordered — not LLM-generated — the same
topic and exclusion set always produce the same query sequence.

*Format honesty.* Discovered resources get `format=None`, **not** the format
that was searched for. Searching for videos does not make every result a
video.

### 6.3 Analysis

**`analysis/resource_analyzer.py`** — cheap, deterministic, runs on every
candidate. Infers `difficulty` from keywords (with `\b` word boundaries) and
`format` from the URL domain.

`FORMAT_DOMAIN_HINTS` covers roughly 60 domains, expanded after real runs
showed most resources labelled "unknown type" — which costs a good resource 30
scoring points. Some entries are judgment calls (`learn.microsoft.com` →
course, `geeksforgeeks.org` → tutorial); these are domain-level facts that can
be defended, not guesses about unseen content.

**YouTube is handled separately from the domain table**, because the same host
serves single videos, playlists, channels and search results. A URL with a
real 11-character video ID is `video`; a `list=` URL with no video ID is
`playlist`; anything else is `None`. A playlist has no single transcript, so
calling it a video would promise analysis the engine cannot deliver.

**`analysis/video_content_analyzer.py`** — real YouTube transcript →
Gemini → timestamped topic chapters.

**`analysis/article_content_analyzer.py`** — real page content (HTML via
BeautifulSoup, or PDF via pypdf) → Gemini → section breakdown, each flagged
`relevant_to_requested_topic`. Capped at 30,000 characters.

**The three analyzers do different jobs despite similar names:**

| File | Question | Cost | Runs on | Uses an LLM? |
|---|---|---|---|---|
| `resource_analyzer.py` | What kind of thing is this? | Free | Every candidate | **No** |
| `video_content_analyzer.py` | What topics, at what timestamps? | Gemini call | One resource | Yes |
| `article_content_analyzer.py` | What sections, relevant to the goal? | Gemini call | One resource | Yes |

`resource_analyzer` produces the two fields feeding **60 of the 100 scoring
points** and contains no LLM. That is the core principle in action.

### 6.4 Verification

Four gates, cheapest first:

1. **Structural** — title, url, topic must be non-empty. Free.
2. **Domain policy** — blocklist check. Free.
3. **Homepage check** — a site's front door is not a resource. Free.
4. **Reachability** — real HTTP GET, status < 400. One network request.

**The homepage gate** was added after a real run recommended
`https://www.geeksforgeeks.org/` — the bare homepage — as a machine learning
resource scoring 50/100, purely because its title contains the word
"learning". A homepage has no specific content, no difficulty and no single
topic; there is nothing to recommend, whatever it scores.

**`verification/domain_policy.py`** holds two lists. `BLOCKED_DOMAINS` covers
piracy sites, social feeds, anonymous free hosting, content farms, and —
added later — **stock media and vendor product pages**, after real runs
surfaced `magnific.com` ("Machine learning Videos - HD and 4K to download")
and `ridgerun.com` (a company's product page) as recommendations.

`TRUSTED_DOMAINS` marks known-good sources but **rejects nothing**. A domain
on neither list is allowed through as neutral. Blocking is deliberate, trust is
a bonus, everything else is permitted — an allowlist-only approach would
starve the catalogue.

**Parallel checking.** The network gate runs across a `ThreadPoolExecutor` with
up to 10 workers. Measured: **7.1× faster** (5.4s → 0.8s on 8 URLs), identical
results, ordering preserved. Threads are correct here specifically because this
is network waiting, not calculation.

### 6.5 Scoring, the topic gate, and the quality floor

**`recommendation/scorer.py`** — plain arithmetic:

| Factor | Points | Awarded when |
|---|---|---|
| Format match | 30 | The learner's format is **known** and matches |
| Level match | 30 | The learner's level is **known** and matches |
| Duration match | 20 | The learner's duration is **known** and matches |
| Goal relevance | 20 | The resource is genuinely about the requested topic |
| **Total** | **100** | |

**The topic gate.** When the learner has named a topic, a resource that is not
about that topic scores **zero**, whatever else it matches. A machine learning
video is not a useful answer to "recommend videos about calculus" just because
the format is right — and a real run returned exactly that, at 30/100, purely
on the format match.

Relevance is judged **semantically**, using the neural embeddings, with a
threshold of 0.45. Exact string matching would reject "machine learning basics"
for a "machine learning" request, throwing away almost the whole catalogue and
forcing a web search on nearly every call.

The gate is applied identically in `scorer.py` and `explanation/decision.py`,
so a record's score and its stated reasons can never disagree. An off-topic
resource's reason reads: *"Not about 'calculus', which is what was requested."*

**The quality floor.** `MIN_RECOMMENDATION_SCORE = 50` in `main.py`. Anything
below is dropped. If **nothing** clears the bar, the best available are
returned anyway with a message saying so — never return nothing when something
exists, but never present a weak match as a good one either.

**`personalization_confidence`** (0.0–1.0) reports how much of the learner's
profile was known, so a low score from an unknown profile is distinguishable
from a low score from a genuine mismatch.

### 6.6 Storage

**`database/persistence.py`** — the **only** module that talks to Postgres.

**`database/resource_store.py`** — the gatekeeper between the pipeline and
stored resources. Loads lazily on first use, caches for the run, falls back to
an in-memory list if the database is unreachable.

### 6.7 Output formatting

**`format_response_as_text()`** in `orchestrator_interface.py` turns the
structured response into readable text.

Deliberately compact. An early version printed every chapter and section with
its full paragraph summary — an eight-section article buried the
recommendations under a wall of text. Now:

- Headings only by default (`SHOW_CONTENT_SUMMARIES = False`)
- Capped at 5 items (`MAX_CONTENT_ITEMS_SHOWN`)
- For articles, the sections flagged relevant to the learner's topic are shown
  first — an eight-section article usually has two that matter
- The "personalization is partial" note is dropped from the cards; it repeated
  on every single one and told the learner nothing actionable

---

## 7. Database schema

Live cloud PostgreSQL on Supabase (free tier). **Four tables.**

### `resources`

```sql
CREATE TABLE resources (
    id                SERIAL PRIMARY KEY,
    title             TEXT NOT NULL,
    url               TEXT NOT NULL UNIQUE,
    description       TEXT,
    topic             TEXT,
    difficulty        TEXT,
    format            TEXT,
    duration          TEXT,
    last_verified_at  TIMESTAMPTZ,
    failed_checks     INTEGER NOT NULL DEFAULT 0
);
```

`UNIQUE` on `url` makes duplicates structurally impossible; with
`ON CONFLICT (url) DO NOTHING`, a repeat discovery is silently skipped rather
than crashing the pipeline.

`difficulty`, `format`, and `duration` are deliberately nullable — a discovered
resource honestly does not know these until analyzed.

### `recommendation_history`

```sql
CREATE TABLE recommendation_history (
    twin_id       TEXT NOT NULL,
    resource_url  TEXT NOT NULL,
    event         TEXT NOT NULL CHECK (event IN ('shown', 'rejected')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (twin_id, resource_url),
    FOREIGN KEY (resource_url) REFERENCES resources (url) ON DELETE CASCADE
);
CREATE INDEX idx_history_twin ON recommendation_history (twin_id);
```

- **Composite primary key** — one row per learner per resource, ever. A learner
  cannot simultaneously be "shown" and "rejected" the same resource; rejecting
  **updates** the existing row. Contradictory state is impossible rather than
  something a query must resolve.
- **Foreign key on `url`, not `id`** — SERIAL ids are reassigned whenever the
  table is rebuilt, which would silently repoint history at wrong resources.
- **`event TEXT` with `CHECK`, not a boolean** — three states are needed: never
  shown (no row), shown (mild), rejected (permanent). `CHECK` also stops typos
  silently never matching.

### `resource_analysis`

```sql
CREATE TABLE resource_analysis (
    resource_url   TEXT PRIMARY KEY,
    analysis_type  TEXT NOT NULL CHECK (analysis_type IN ('video', 'article')),
    analysis_json  TEXT NOT NULL,
    analyzed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

A shared cache: an analysis paid for by any learner is reused by every other.
**No foreign key** — the analysis may be requested for a pasted URL not in the
catalogue, and stays valid if the resource leaves it.

Only **successful** analyses are cached. Caching a failure would freeze a
temporary outage permanently. This proved its worth immediately: a Gemini
`503 UNAVAILABLE` was served correctly from cache moments later.

### `extraction_cache`

```sql
CREATE TABLE extraction_cache (
    input_hash       TEXT PRIMARY KEY,
    extraction_kind  TEXT NOT NULL CHECK (extraction_kind IN ('briefing', 'request')),
    extracted_json   TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Keyed by a SHA-256 hash of the input text — a briefing can be thousands of
characters, far too long for a primary key.

Three benefits: fewer API calls; a repeat request survives a Gemini outage; and
it closes a reproducibility gap, since the same briefing now always yields the
same extraction.

---

## 8. Integration contract

### The two-string entry point

```python
from orchestrator_interface import recommend_text

text = recommend_text(briefing_string, user_request_string)
```

**Two inputs, both strings, both matter:**

- `briefing` — the ContextBuilder output. Stored long-term state.
- `user_request` — what the learner just typed.

Optional: `something_else=True` (exclude everything already shown),
`include_content=False` (skip analysis, faster).

**Output:** ready-to-display text.

### The structured variant

```python
from orchestrator_interface import recommend_from_briefing

response = recommend_from_briefing(briefing, user_request)
```

Returns a dict — use this when the interface needs individual fields for
clickable links, score badges, or a reject button. Those cannot be recovered
reliably from formatted text.

```python
{
    "status": "ok",
    "intent": "resource_recommendation",
    "recommendations": [
        {
            "resource": "title",
            "url": "https://...",
            "format": "video",
            "score": 80,
            "score_breakdown": {"format_match": 30, "level_match": 30,
                                "duration_match": 0, "goal_relevance": 20},
            "reasons": ["Matches the learner's preferred format", "..."],
            "personalization_confidence": 1.0
        }
    ],
    "content": {"access_status": "ok", "chapters": [...]},
    "content_for_url": "https://...",
    "message": "OK",
    "warnings": []
}
```

**`content_for_url`** names which resource the analysis belongs to. Match on
this rather than assuming item #1 — if ranking changes, matching by URL keeps
the display correct.

### Three intents (full dict interface)

`handle_orchestrator_request()` supports:

- **`resource_recommendation`** — the main path
- **`reject_resources`** — permanently exclude resources for a learner
- **`analyze_resource_content`** — deep analysis of one chosen resource. Built
  for a per-resource "What's inside?" button; **not currently used by the UI**,
  which shows analysis for the top result automatically. Kept working and
  tested so the button can be added with no engine changes.

### What the Orchestrator must do

1. **Send `twin_id`** in the briefing or learner state. See Section 14.
2. **Set `something_else` with the LLM, not keywords.** When a learner asks for
   different resources — any phrasing, any language — the Orchestrator's model
   should recognise that. This engine does no language understanding on intent,
   by design.
3. **Show a loading state.** A first request on a new topic takes 30–60 seconds
   while the engine searches and verifies the live internet. Later requests on
   the same topic are fast.
4. **Understand the engine is deterministic.** Same input, same output. Variety
   requires `something_else=True`.

---

## 9. File structure

```
recommendation_system/          (at src/agents/recommendation_system/ in EduTwin)
├── main.py                     pipeline, request overlay, history, analysis routing
├── config.py                   known values and field aliases
├── orchestrator_interface.py   entry points, three intents, text formatting
├── reverify.py                 periodic catalogue audit (run on a schedule)
├── models/
│   └── resource.py             Resource class, to_dict / from_dict
├── twin/
│   ├── mock_twin.py            mock Digital Twin + normalization adapter
│   ├── context_extractor.py    briefing → learner state (cache → Gemini)
│   └── request_extractor.py    message → request (cache → Gemini → keywords)
├── retrieval/
│   ├── search_requirement.py
│   ├── retriever.py            five-tier fallback + discover_and_store
│   ├── semantic.py             bag-of-words fallback
│   ├── embeddings.py           real neural embeddings
│   └── discover.py             internet discovery + query variation
├── database/
│   ├── resource_store.py       catalogue gatekeeper, lazy load + cache
│   ├── persistence.py          THE only module that talks to Postgres
│   ├── create_table.py         resources (DESTRUCTIVE — drops first)
│   ├── create_history_table.py recommendation_history (safe)
│   ├── create_analysis_table.py resource_analysis (safe)
│   ├── create_extraction_table.py extraction_cache (safe)
│   └── add_verification_columns.py migration: re-verification tracking
├── verification/
│   ├── verifier.py             four gates, parallel network checks
│   └── domain_policy.py        blocklist / trustlist
├── recommendation/
│   ├── scorer.py               100-point arithmetic, topic gate, confidence
│   └── engine.py               ranking
├── explanation/
│   └── decision.py             structured decision records
└── analysis/
    ├── resource_analyzer.py          difficulty/format inference (no LLM)
    ├── video_content_analyzer.py     YouTube transcript → Gemini chapters
    └── article_content_analyzer.py   article/PDF text → Gemini sections
```

Every package folder also contains `__init__.py`.

**Import convention:** all imports use the full repo path
(`from src.agents.recommendation_system.x import y`) and the project runs from
the **repo root**, not from inside `recommendation_system`. This changed
partway through development and caused several failures where individual files
still used the old short-path style. If a `ModuleNotFoundError` names one of
this project's own packages, that file is on the wrong convention.

**Deleted during cleanup:** `analysis/test_connection.py` and
`retrieval/test_retrieval.py` — untracked scratch files, both stale. Component
tests now live in `if __name__ == "__main__":` blocks inside the modules they
test, so they cannot drift out of sync.

---

## 10. Running the project

### Environment variables

Never hardcoded in any file.

```powershell
$env:DB_HOST     = "aws-0-<region>.pooler.supabase.com"
$env:DB_USER     = "postgres.<project-ref>"
$env:DB_PORT     = "5432"
$env:DB_NAME     = "postgres"
$env:DB_PASSWORD = "..."
$env:GEMINI_API_KEY = "..."
```

**Set these permanently** through Windows System Properties. Using `$env:` per
window loses them on every restart, and this caused four separate debugging
sessions — including one where a silent fallback to `localhost` made it look
like a database outage.

Two traps, both hit in real use:

- **`DB_NAME` is always `postgres`.** The project reference goes on the
  **username** only. Putting it in `DB_NAME` gives
  `database "postgres.<ref>" does not exist`.
- **Type each on ONE line.** Pressing Enter after the opening quote stores a
  leading newline in the value, producing `user not found in the database` even
  though the value looks correct.

### First-time setup

```
py src\agents\recommendation_system\database\create_table.py
py src\agents\recommendation_system\database\create_history_table.py
py src\agents\recommendation_system\database\create_analysis_table.py
py src\agents\recommendation_system\database\create_extraction_table.py
py src\agents\recommendation_system\database\add_verification_columns.py
```

Order matters: the history table's foreign key requires `resources` to exist.

**`create_table.py` is destructive.** It runs `DROP TABLE ... CASCADE`, which
also drops `recommendation_history`. Re-run `create_history_table.py` after.

### Routine operation

```
py -m src.agents.recommendation_system.main                   # pipeline scenarios
py -m src.agents.recommendation_system.orchestrator_interface # integration tests
py -m src.agents.recommendation_system.twin.request_extractor # extraction, incl. fallback
py -m src.agents.recommendation_system.reverify               # catalogue audit
```

`reverify.py` should run on a schedule (weekly), never during a request. Its
`__main__` block passes `max_age_days=0` to force everything due — right for
testing, wrong for scheduled use.

---

## 11. Real bugs hit and fixed

### Correctness

**Format assumed rather than verified.** *(Most significant.)* `discover.py`
set `format=requested_format` — "we searched for videos, so this is a video."
Every discovered resource collected **30 unearned points**. Real examples
falsely claiming to be videos: a YouTube playlist, a TikTok discovery page, two
documentation pages, a category listing. Fixed by leaving format `None` at
discovery and inferring conservatively from the URL, with YouTube path
inspection.

**Off-topic resources scoring well.** A calculus request returned all 47
machine learning resources at 30/100 each. Two causes, both fixed: tier 4
matched everything before discovery could run, and format-only matches scored
30 with no topic requirement. Fixed by the tier 4 guard and the topic gate.

**Site homepage recommended.** `geeksforgeeks.org/` scored 50/100 for a machine
learning request because its title contains "learning". Fixed with a homepage
gate in the verifier.

**Keyword fallback destroyed subject names.** `"learning"` was in
`NOISE_WORDS`, so `"machine learning"` became `"machine"` — and the engine
recommended a **sewing machine tutorial**. Fixed by removing "learn"/"learning"
from the noise list.

**Keyword fallback returned a marker word as the topic.** `"recommend
something for me"` produced `topic: "for"`, and the engine searched the web for
`"for beginner video"`. Fixed by excluding marker words from the topic.

**Keyword false positive.** A naive substring check matched `"intro"` inside
`"introducing"`. Fixed with `\b` word boundaries.

**Single recommendation returned.** Discovery stopped after 5 candidates;
verification rejected 4. Fixed by searching in rounds until enough *survive*.

**Verified work discarded.** Surplus resources that had each cost a network
request were thrown away. Fixed by saving everything verified and returning
only what the request needs.

**26 recommendations returned.** Tier 1 returns everything matching, and the
catalogue grows every run. Worse, all 26 were recorded as "shown", wrongly
excluding 21 good resources from every future request. Fixed by capping
**before** recording history.

**Duplicate entries winning the sort.** Fixed by deletion and prevented
permanently by the `UNIQUE` constraint.

### Environment and tooling

**Import convention drift.** Files mixing short paths
(`from retrieval.semantic import ...`) with full repo paths caused
`ModuleNotFoundError`. One was especially hard to find: `embeddings.py` line 69
had a bad import **inside a function body**, so it only fired when called —
producing the misleading message `Neural embeddings unavailable (No module
named 'retrieval')` and a silent fallback to bag-of-words for days.

**Files documented but absent.** `Resource.from_dict()`,
`analysis/resource_analyzer.py`, and later the extraction-cache functions were
all described as complete but were not on disk. Verify against the filesystem.

**Three distinct network-level failures on the same wifi:**

1. **TLS interception** — all HTTPS failed with `CERTIFICATE_VERIFY_FAILED` /
   `invalid peer certificate: UnknownIssuer`. Certificate verification was
   deliberately **not** disabled; for a system whose purpose is verifying
   resources, that would be the wrong trade.
2. **IPv6 routing** — the direct Supabase host resolves to IPv6 only, which
   many networks cannot route. Fixed by switching to the session pooler
   (IPv4). Environment variables only; no code changes.
3. **Outbound port blocking** — `Test-NetConnection` to the pooler failed on
   both TCP 5432 and ICMP ping, from a `172.18.x.x` private address. Not a
   paused project; the network drops the traffic. Workaround: phone hotspot.

**Gemini API failures**, twice, in normal use: `429 RESOURCE_EXHAUSTED` (free
tier is 20 requests/day/model) and `503 UNAVAILABLE` (overloaded). Each
recommendation makes up to 4 Gemini calls, so the daily quota is roughly 5 test
runs. This directly motivated the extraction cache and keyword fallback.

**Windows case-sensitivity vs Python imports** — folders named `Twin`/`DataBase`
caused import failures; fixed with a two-step rename.

**Wikipedia 403** — the default User-Agent looked bot-like. Fixed with a
browser-like header.

**Dependency issues** — `gemini-2.5-flash` deprecated (→ `gemini-3.5-flash`);
`duckduckgo_search` renamed to `ddgs`; `google-generativeai` superseded by
`google-genai`; Supabase connection string broken by `@`, `[`, `]` in the
password (fixed with separate arguments).

### Security

One real API key was accidentally pasted into a chat and was revoked and
regenerated. **Team Alpha's knowledge graph file assigns `GOOGLE_API_KEY`
directly in code** — if a real key was ever committed, it remains in git
history even after deletion. This should be checked.

---

## 12. Known limitations

**Duration is never inferred.** Nothing determines whether a resource is short,
medium or long, so every resource forfeits 20 of 100 points and realistic
scores cap at 80.

**No quality signal in scoring.** Among resources that pass the topic gate,
nothing distinguishes an excellent resource from a mediocre one — no view
counts, no reputation, no ratings. `TRUSTED_DOMAINS` exists and is **not wired
into scoring**; doing so is the most obvious next improvement.

**Non-educational topics rank poorly.** A request for football or gaming
content extracts correctly, but most such content lives on blocked social
domains, and with no quality signal every result caps at 30. The engine is
tuned for educational topics; this is a scope boundary, not a bug.

**Score ties are broken arbitrarily.** Python's sort is stable, so the winner
among equal scores is whichever came out of Postgres first — insertion order,
not merit.

**Prose extraction is not fully reproducible.** The same briefing may yield a
different level or format. The recommendation decision remains deterministic
*given* a learner state; it is extraction that varies. The extraction cache
fixes this for inputs seen before.

**Goal selection is an LLM judgment.** When the Twin holds several goals, the
extractor picks one. Team Alpha's `Goal` model has `GoalPriority` and
`GoalStatus` — if the briefing exposed which goal is active, this could be
deterministic instead.

**The keyword fallback is crude by design.** It handles common shapes
("10 videos about calculus") but would fail on a long conversational message.
It only runs when Gemini is unavailable.

**Blocklist maintenance is ongoing.** New junk domains appear continuously —
piracy sites, then a video scraper, then stock-media libraries. This is a list
that needs periodic curation.

**The blocklist uses substring matching.** `if domain in url` would also match
`notreddit.com.example.org`. Sufficient for filtering search results,
insufficient against a determined actor.

**Cached analyses never expire.** `analyzed_at` is stored but no policy uses it.

**Deleting a resource erases learner history for it** via `ON DELETE CASCADE`,
including rejections.

**Degraded mode is non-deterministic.** With Postgres unreachable, discovery
adds to the in-memory cache mid-session, so later requests see a different
catalogue than earlier ones.

**Books are out of scope** by deliberate team decision — copyrighted or
paywalled with no legitimate full-text access. They receive an honest "not yet
supported" message.

---

## 13. External dependencies

| Library | Purpose | Notes |
|---|---|---|
| `psycopg2-binary` | PostgreSQL connectivity | |
| `sentence-transformers` | Neural embeddings | `all-MiniLM-L6-v2`, runs locally |
| `ddgs` | Internet search | **Not** the old `duckduckgo_search` |
| `requests` | HTTP verification and fetching | Needs a browser-like User-Agent |
| `youtube-transcript-api` | YouTube transcripts | Unofficial; can be rate-limited |
| `google-genai` | Gemini API | **Not** `google-generativeai` |
| `beautifulsoup4` | HTML parsing | |
| `pypdf` | PDF text extraction | |

One install line:

```
py -m pip install sentence-transformers requests ddgs google-genai youtube-transcript-api beautifulsoup4 pypdf psycopg2-binary
```

The wider EduTwin project also needs `chromadb`, `matplotlib`, and `networkx`.
**The team has no `requirements.txt`** — everyone installs packages one at a
time as errors appear. This should be fixed.

---

## 14. THE BLOCKING INTEGRATION ISSUE

**`twin_id` is never supplied by the live briefing.**

Every test through the real Orchestrator returns:

```
[context extractor] Extracted: {'twin_id': None, 'goal': ..., ...}
```

The briefing contains a name, university, field of study and education stage —
but no learner identifier.

**Consequence:** the entire learner memory system does nothing in the live
system.

- Already-seen resources are not excluded
- Rejections fail outright (`A twin_id is required to record rejections`)
- "Recommend something else" returns the same results
- Nothing is recorded between sessions

This is the feature that most directly demonstrates the research question, and
in the integrated system it is **inert**.

**It cannot be fixed from inside this component.** The engine already accepts
four field names (`twin_id`, `learner_id`, `student_id`, `id`) and warns when
none is present. The Orchestrator must include `StudentTwin.twin_id` in the
briefing, or pass it alongside.

**This is the single highest-priority open item.**

---

## 15. Other questions outstanding for the team

**For the Orchestrator builder:**

1. Will `twin_id` be included? (Section 14.)
2. Confirm the LLM — not a keyword list — sets `something_else`.
3. Do you want the per-resource "What's inside?" button? The intent is built
   and tested but unused.

**For the Digital Twin owner:**

4. Are the `Evidence.content` strings in the TWIN section stable in wording? If
   fields appeared as consistent lines like `Level: beginner`, extraction could
   be deterministic with **no LLM call at all** — faster, free, fully
   reproducible, and no Gemini dependency on the primary path. This would
   materially strengthen the research claim.
5. Does the briefing expose which goal is current or primary? See Section 12.
6. If a learner rejects resources, should the engine emit a `Memory` so the
   Twin Updater can learn from it? The history table drives filtering; a Memory
   would carry the signal upstream.

**For the knowledge graph owner:**

7. Is the graph persisted, or rebuilt each run? Is `mastery` ever populated?
8. Can the module-level `nx.draw_spring(G)` / `mtl.show()` calls move into a
   `__main__` block? Importing the file currently opens a blocking plot window.
9. Please check for a committed API key.

---

## 16. Suggested next steps

**Immediate:**

1. **Resolve `twin_id`** with the Orchestrator builder. Nothing else matters as
   much.
2. **Test end-to-end persistence on an unrestricted network** — discover, save,
   restart, confirm the resources are still there.
3. **Create a `requirements.txt`** for the whole project.

**Short-term, in value order:**

4. **Wire `TRUSTED_DOMAINS` into scoring** as a quality signal and a tiebreaker.
   The single biggest available improvement to recommendation quality.
5. **Infer duration** — recovers 20 points currently forfeited on every
   resource.
6. **Continue curating the blocklist** as new junk domains appear.

**Parked, discussed but not built:**

7. **Blended recommendations** — after the requested topic, add 2–3 resources
   relevant to the learner's stored goal, clearly labelled. Discussed; the
   ambitious version (recommending linear algebra because it supports machine
   learning) needs prerequisite knowledge the engine does not have. The simpler
   version needs no new knowledge and works today.
8. **"First query fails in the GUI"** — reported but never diagnosed; the
   failure output was never captured. Likely a timeout on the slow first
   request, but unconfirmed.

**Longer-term, dependent on other teams:**

9. Real Digital Twin integration — `goals: dict[UUID, Goal]` vs a single string.
10. Knowledge graph integration — blocked on persistence and mastery.
11. Staleness policy for cached analyses.

---

## 17. Design principles worth preserving

**Never claim what you have not verified.** The format bug awarded 30 points
for an assumption. Every field is either known and correct, or `None`. `None`
scores zero, which is the honest outcome.

**A wrong answer is worse than no answer.** The topic gate and the score floor
both exist because returning something plausible-but-irrelevant wastes the
learner's time and makes the engine look careless. But never return nothing
when something exists — say plainly that the matches are weak.

**Make invalid states structurally impossible.** The composite primary key
means a learner cannot be both shown and rejected the same resource. The
`UNIQUE` constraint means duplicates cannot accumulate. Rules enforced by the
database survive buggy code, other people's scripts, and manual edits.

**Degrade honestly, never crash.** Every external dependency has a fallback
that explains itself. Validated repeatedly by real network, database and API
failures — the engine kept working and said exactly what was wrong.

**Layer the fallbacks.** Cache, then API, then deterministic code. Each layer
is cheaper and more reliable than the one before it.

**Cheapest checks first.** Structural, blocklist and homepage checks run before
any network request. Cache lookups run before any API call.

**Pay once, share the result.** Verified resources and content analyses go into
shared tables. Work done for one learner benefits every learner.

**Reproducibility is a feature.** Same input, same output — so a recommendation
can be explained, audited, and defended.

**Documentation drifts; the filesystem does not.** Several files this project's
own notes described as complete were not on disk. Verify before trusting.

**Say when you do not know.** Several bugs were diagnosed only after asking for
the actual output rather than guessing from a description.