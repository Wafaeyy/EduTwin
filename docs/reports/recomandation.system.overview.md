Team Beta — Resource Recommendation Engine
Complete project context and technical handover.
This document describes everything built, decided, and still open for the
Recommendation Engine component of the EduTwin multi-agent educational system.
It is written to be handed to another AI assistant or teammate as complete
context, or kept as a personal reference.
---
1. Who is building this, and how they learn
Builder: a Computer Engineering student, working as a researcher in an
8-week AI research internship, part of Team Beta.
Python knowledge: near-zero at the start of this project. Learned Python
fundamentals (variables, functions, dictionaries, lists, loops, conditionals,
classes, modules/packages, `try`/`except`, regex, JSON, SQL, threading)
progressively, alongside building this real system — not through toy examples.
How this person needs to be taught, if you are continuing this work:
Explain every new concept from zero, assuming no prior Python background, in
very simple, beginner-friendly language.
After every step, provide the whole current file's code (not just a
diff or snippet) and say exactly which file path to put it in. Giving a
fragment with "add this below function X" has repeatedly caused the change
to be missed — provide complete files.
Explain code line by line, in simple terms.
Give direct, honest feedback — including admitting bugs and fixing them
transparently. Several real bugs were found this way; see Section 10.
Prefer concrete worked examples over abstract explanations.
Move at a deliberate pace: one component at a time, tested before moving on.
Explain the "why" before the "what." Handing over a file without first
explaining what problem it solves does not work — this was tried and had to
be redone.
This person is not on Team Alpha (who build the Digital Twin) and is not the
Orchestrator builder (a teammate owns that) — this person owns the
Recommendation Engine specifically.
---
2. The project
Research question
> How should AI agents consume a continuously evolving Digital Twin to produce
> personalized, explainable, and adaptive educational guidance that outperforms
> a traditional stateless LLM assistant?
Core thesis: personalization should be an architectural property of the AI
system, not merely a prompt-engineering trick.
System context
Team Alpha owns the Digital Twin (the evolving learner model), a Memory
System, and a knowledge graph.
Team Beta designs the AI reasoning architecture that consumes the Digital
Twin — multi-agent architecture, context engineering, recommendation systems,
explainability, adaptive personalization.
This component: the Resource Recommendation Engine — recommends
educational resources (videos, books, courses, articles, tutorials,
documentation, research papers, practice platforms) that are genuinely
useful, verified, accessible, and personalized.
A teammate is building the Orchestrator, which routes learner requests to
the right agent.
Core architectural principle (non-negotiable)
LLMs must NOT make the final recommendation decision.
LLMs are used only for:
understanding natural-language requests (the Orchestrator),
extracting structured fields from prose (the context extractor),
understanding unstructured resource content (video transcripts, article text),
generating natural-language explanations.
All filtering, scoring, ranking, and the final recommendation decision are
100% deterministic code — reproducible, explainable, debuggable. This is
why the scoring system is plain arithmetic and never "ask an LLM which is best."
Where this principle showed its value: a real bug was found where every
discovered resource claimed to be a video and collected 30 unearned scoring
points. Because scoring is transparent arithmetic with a printed breakdown, the
bug was visible in the output. An LLM-scored system would have hidden it.
---
3. How the engine demonstrates the research question
The clearest demonstration of "outperforms a stateless LLM assistant" is the
learner history system:
	Stateless LLM assistant	This engine
Learner asks twice	May give different answers randomly	Identical answer, by design
Learner says "recommend something else"	Often repeats itself — no memory of what it said	Excludes everything shown, searches with varied queries for genuinely new material
Learner rejects a resource	Forgotten immediately	Permanently excluded, across sessions, stored in Postgres
Learner asks why	Post-hoc rationalization	Exact score breakdown: `format 30 | level 30 | duration 0 | goal 20`
Reproducibility is deliberate, not accidental. Same learner + same question =
same answer, so a recommendation can always be explained and audited. Variety
is available but must be explicitly requested via `exclude\_seen`.
---
4. The pipeline, end to end
A single call to `handle\_orchestrator\_request()` runs all of this:
```
Request arrives
  ↓ validate intent and shape
  ↓ resolve learner\_state (structured, or LLM-extracted from prose briefing)
  ↓ normalize (field aliases, reject invalid values)
  ↓ load this learner's history from Postgres
  ↓ build search requirement (topic, level, format)
  ↓
  ├─ TIER 1: exact topic + exact level      ┐
  ├─ TIER 2: exact topic, any level         │ each filtered against history;
  ├─ TIER 3: semantic (neural embeddings)   │ stops at the first tier that
  ├─ TIER 4: entire catalog                 │ yields unseen resources
  └─ TIER 5: external internet discovery    ┘
        ├─ query variation (6 templates, escalating)
        ├─ analyze (infer difficulty and format)
        ├─ verify (structural → blocklist → parallel HTTP)
        └─ save all verified to Postgres
  ↓ score every resource (format 30 / level 30 / duration 20 / goal 20)
  ↓ rank by score
  ↓ record what was shown
  ↓ deep content analysis of the TOP resource only (cached, shared)
  ↓ return structured response
```
Tier fallback logic: each tier is a deliberate relaxation of constraints.
The engine never returns nothing when something reasonable exists, but never
pretends a loose match is a tight one — the scorer downgrades weak matches
honestly rather than inflating them.
---
5. Component reference
5.1 Learner state handling
`twin/mock\_twin.py` — `get\_relevant\_digital\_twin\_state()` stands in for
Team Alpha's real Digital Twin. `normalize\_learner\_state()` is the adapter
layer: it maps field aliases (`current\_skill\_level` → `level`), rejects values
outside the known lists, and returns a clean predictable shape.
`config.py` — the single source of truth for `KNOWN\_LEVELS`,
`KNOWN\_FORMATS`, `KNOWN\_DURATIONS`, and `FIELD\_ALIASES`. Every module checks
against these, so adding a new valid value means changing one file.
`twin/context\_extractor.py` — the Orchestrator's `ContextBuilder` produces
a prose string written for LLM agents, not a structured dict. This module
makes a Gemini call to extract the five fields the engine needs.
Guardrails, all enforced by deterministic code around the call:
The prompt injects the actual `KNOWN\_\*` constants, so it cannot drift from
`config.py`.
The model is instructed to return `null` rather than guess.
Only the five expected keys are kept; anything else the model adds is
discarded before it reaches the engine.
Output still passes through `normalize\_learner\_state()`, so the model cannot
introduce a value the engine would not otherwise accept.
Every failure path returns `{}` — missing API key, Gemini down, unparseable
JSON, non-dict response.
Truncation at 20,000 characters is safe because `ContextBuilder` emits
`STUDENT PROFILE \& TWIN` first, always (hardcoded section order). Truncation
loses memories and graph knowledge, never the profile fields.
5.2 Retrieval
`retrieval/search\_requirement.py` — converts learner state into a search
description: topic, level, format.
`retrieval/retriever.py` — the five-tier fallback ladder, plus
`discover\_and\_store()`. Every tier is filtered against the learner's history
via `exclude\_seen()`, which is what makes an exhausted learner fall through to
discovery rather than receiving nothing.
`retrieval/semantic.py` — bag-of-words vectors with real cosine similarity
math, built from first principles (dot product, magnitude, cosine formula).
Used as an automatic fallback.
`retrieval/embeddings.py` — real neural embeddings via
`sentence-transformers` (`all-MiniLM-L6-v2`), running locally after a one-time
model download. The system tries this first at startup and falls back to
bag-of-words if the model cannot load, printing which one is active.
`retrieval/discover.py` — real internet search via `ddgs` (DuckDuckGo).
Two important behaviours:
Query variation. Six fixed templates, tried in order, stopping as soon as
enough new candidates are found:
`{topic} {level} {format}`
`learn {topic} from scratch {format}`
`{topic} crash course {format}`
`best {format} to learn {topic}`
`{topic} explained step by step {format}`
`{topic} full guide {format}`
In the normal case only template 1 runs. When a learner has seen everything the
obvious search returns, later templates fire automatically and find genuinely
different material. Because the list is fixed and ordered — not LLM-generated —
the same topic and same exclusion set always produce the same query sequence.
Format honesty. Discovered resources get `format=None`, not the format
that was searched for. Searching for videos does not make every result a video;
search engines return playlists, category pages, and articles about videos.
5.3 Analysis
`analysis/resource\_analyzer.py` — cheap, deterministic, runs on every
candidate. Infers `difficulty` from keywords (with `\\b` word boundaries, so
"intro" does not match inside "introducing") and `format` from the URL domain.
Format inference is deliberately conservative and returns `None` when unsure.
YouTube is handled separately from the general domain table, because the same
host serves single videos, playlists, channels, and search results — only a URL
containing a real 11-character video ID is called a video.
`analysis/video\_content\_analyzer.py` — fetches a real YouTube transcript
(`youtube-transcript-api`), formats it with timestamps, sends it to Gemini with
a JSON-only instruction, and parses back timestamped topic chapters.
`analysis/article\_content\_analyzer.py` — fetches real page content (HTML via
`requests` + `BeautifulSoup`, or PDF via `pypdf`), strips nav/script/style
clutter, and gets back a section-by-section breakdown with each section flagged
`relevant\_to\_requested\_topic: true/false`. Capped at 30,000 characters.
The distinction between the three analyzers matters and the names are
confusing:
File	Question it answers	Cost	Runs on	Uses an LLM?
`resource\_analyzer.py`	What kind of thing is this?	Free	Every candidate	No
`video\_content\_analyzer.py`	What topics, at what timestamps?	Gemini call	One resource	Yes
`article\_content\_analyzer.py`	What sections, relevant to the goal?	Gemini call	One resource	Yes
`resource\_analyzer` produces `difficulty` and `format` — the two fields feeding
60 of the 100 scoring points — and contains no LLM. That is the core
principle in action.
5.4 Verification
Three gates, cheapest first, so a network request is never spent on a resource
that was always going to be rejected:
Structural — title, url, and topic must be non-empty. Free.
Domain policy — `verification/domain\_policy.py`. Free.
Reachability — a real HTTP GET, status < 400. Costs a network request.
`verification/domain\_policy.py` holds two lists. `BLOCKED\_DOMAINS` covers
piracy sites, social feeds, anonymous free hosting, and content farms — real
discovery runs surfaced `scanlibs.com` (pirated courses), TikTok discovery
pages, and anonymous `.netlify.app` subdomains alongside good material.
`TRUSTED\_DOMAINS` marks known-good educational sources but rejects nothing;
a domain on neither list is allowed through as neutral. Blocking is deliberate,
trust is a bonus, everything else is permitted — an allowlist-only approach
would starve the catalog.
Parallel checking. `verify\_resources()` runs the network gate across a
`ThreadPoolExecutor` with up to 10 workers. Verifying 15 URLs one at a time
means adding up 15 waits (two minutes in real runs, since a dead link burns the
full 5-second timeout). Measured result: 7.1× faster, with identical
results and preserved ordering.
Threads are correct here specifically because this is network waiting, not
calculation — Python releases the GIL while waiting on a socket. Order is
preserved because `pool.map()` returns results in input order regardless of
which thread finished first, and ranking depends on order (ties keep their
original placement).
5.5 Scoring and explanation
`recommendation/scorer.py` — plain arithmetic:
Factor	Points	Awarded when
Format match	30	The learner's format is known and matches
Level match	30	The learner's level is known and matches
Duration match	20	The learner's duration is known and matches
Goal relevance	20	The learner's goal is known and matches the topic
Total	100	
A factor only earns points if the learner's value is known and matches. It
never guesses a match for missing data. `personalization\_confidence` (0.0–1.0)
reports how much of the learner's profile was actually known.
`explanation/decision.py` — builds structured decision records. Reasons are
generated directly from the score breakdown, never invented.
`recommendation/engine.py` — sorts decision records by score, highest first.
5.6 Storage
`database/persistence.py` — the only module that talks to Postgres.
Everything else goes through its functions.
`database/resource\_store.py` — the gatekeeper between the pipeline and
stored resources. Loads from Postgres lazily on first use, caches for the run,
and falls back to an in-memory list if the database is unreachable. Nothing
outside this module touches the resource list directly.
---
6. Database schema
Live cloud PostgreSQL, hosted on Supabase (free tier).
`resources`
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
    last\_verified\_at  TIMESTAMPTZ,
    failed\_checks     INTEGER NOT NULL DEFAULT 0
);
```
`UNIQUE` on `url` is what makes duplicates structurally impossible; combined
with `ON CONFLICT (url) DO NOTHING`, a repeat discovery is silently skipped
rather than crashing the pipeline.
`difficulty`, `format`, and `duration` are deliberately nullable — a discovered
resource honestly does not know these until analyzed, and the table must be
able to store that honest unknown.
`recommendation\_history`
```sql
CREATE TABLE recommendation\_history (
    twin\_id       TEXT NOT NULL,
    resource\_url  TEXT NOT NULL,
    event         TEXT NOT NULL CHECK (event IN ('shown', 'rejected')),
    created\_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated\_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (twin\_id, resource\_url),

    FOREIGN KEY (resource\_url)
        REFERENCES resources (url)
        ON DELETE CASCADE
);

CREATE INDEX idx\_history\_twin ON recommendation\_history (twin\_id);
```
Design decisions, each deliberate:
Composite primary key `(twin\_id, resource\_url)` — one row per learner per
resource, ever. A learner cannot simultaneously be "shown" and "rejected" for
the same resource; rejecting updates the existing row. This makes
contradictory state structurally impossible rather than something the query
layer has to resolve.
Foreign key on `url`, not `id` — `SERIAL` ids are reassigned whenever the
resources table is rebuilt, which would silently corrupt history. URLs are
stable, and `resources.url` is `UNIQUE`, so it is a valid FK target.
`event TEXT` with a `CHECK`, not a boolean — three states are needed:
never shown (no row), shown (mild signal), rejected (permanent). A boolean
cannot express that, and `CHECK` stops typos like `'Shown'` or `'rejcted'`
silently never matching a query.
`ON DELETE CASCADE` — deleting a resource removes its history. See
Section 11 for the consequence.
`resource\_analysis`
```sql
CREATE TABLE resource\_analysis (
    resource\_url   TEXT PRIMARY KEY,
    analysis\_type  TEXT NOT NULL CHECK (analysis\_type IN ('video', 'article')),
    analysis\_json  TEXT NOT NULL,
    analyzed\_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```
A shared cache. An analysis paid for by any learner is reused by every other
learner. No foreign key to `resources` — deliberate, because the analysis
may be requested for a URL the learner pasted in, and it stays valid even if
the resource leaves the catalog.
Only successful analyses are cached. Caching a failure would freeze a
temporary Gemini outage permanently, and the resource could never be analyzed
again. This proved its worth immediately: a Gemini `503 UNAVAILABLE` failure was
served correctly from cache moments later.
---
7. Integration contract for the Orchestrator
Single entry point:
```python
from orchestrator\_interface import handle\_orchestrator\_request
response = handle\_orchestrator\_request(request)
```
This runs the entire pipeline. Nothing else needs to be called.
Intent 1 — `resource\_recommendation`
```python
{
    "intent": "resource\_recommendation",
    "learner\_state": {
        "twin\_id": "3f2a8c91-...",
        "level": "beginner",
        "goal": "machine learning",
        "preferred\_format": "video",
        "preferred\_duration": "short"
    },
    "context": "<prose briefing, used only if learner\_state is absent>",
    "user\_request": "recommend something else",
    "exclude\_seen": true,
    "include\_content": true
}
```
Intent 2 — `reject\_resources`
```python
{
    "intent": "reject\_resources",
    "learner\_state": {"twin\_id": "3f2a8c91-..."},
    "resource\_urls": \["https://...", "https://..."]
}
```
Intent 3 — `analyze\_resource\_content`
```python
{
    "intent": "analyze\_resource\_content",
    "resource\_url": "https://...",
    "format": "video",
    "topic": "machine learning"
}
```
Built for a per-resource "What's inside?" button so the learner can pick which
resource to explore. Not currently used by the UI — the current design
returns analysis for the top recommendation automatically. Kept working and
tested so the button can be added with no engine changes.
Response — same shape every time, success or failure
```python
{
    "status": "ok",                    # or "error"
    "intent": "resource\_recommendation",
    "recommendations": \[
        {
            "resource": "title",
            "url": "https://...",
            "format": "video",
            "score": 80,
            "score\_breakdown": {
                "format\_match": 30, "level\_match": 30,
                "duration\_match": 0, "goal\_relevance": 20
            },
            "reasons": \["Matches the learner's preferred format", "..."],
            "personalization\_confidence": 1.0
        }
    ],
    "content": {"access\_status": "ok", "chapters": \[...]},
    "content\_for\_url": "https://www.youtube.com/watch?v=...",
    "message": "OK",
    "warnings": \[]
}
```
`content\_for\_url` names which resource the content belongs to. The UI should
match on this rather than assuming item #1 — if ranking ever changes, matching
by URL keeps the display correct.
The Orchestrator never receives an exception. Infrastructure failures come back
as `status: "error"` with a message.
Three requirements for the Orchestrator builder
Send `twin\_id` in `learner\_state`. Without it the engine cannot remember
anything — no history, no exclusions, and rejections fail outright. The
engine accepts `twin\_id`, `learner\_id`, `student\_id`, or `id`.
The Orchestrator sets `exclude\_seen`, not the engine. When the learner
wants different resources — "show me others", "these are boring", any
phrasing in any language — the Orchestrator's LLM understands that and sets
the flag. The engine performs no language understanding on the user's
request, by design. This must be model understanding, not a keyword list.
The engine is deterministic. Same learner + same question = same answer,
on purpose. Variety comes only from `exclude\_seen: true`.
---
8. File structure
```
recommendation\_system/          (at src/agents/recommendation\_system/ in EduTwin)
├── main.py                     pipeline entry, history read/write, analysis routing
├── config.py                   known values and field aliases
├── orchestrator\_interface.py   the Orchestrator's front door — three intents
├── reverify.py                 periodic catalog audit (run on a schedule)
├── models/
│   ├── \_\_init\_\_.py
│   └── resource.py             Resource class, to\_dict / from\_dict
├── twin/
│   ├── \_\_init\_\_.py
│   ├── mock\_twin.py            mock Digital Twin + normalization adapter
│   └── context\_extractor.py    LLM extraction of learner state from prose
├── retrieval/
│   ├── \_\_init\_\_.py
│   ├── search\_requirement.py
│   ├── retriever.py            five-tier fallback + discover\_and\_store
│   ├── semantic.py             bag-of-words fallback
│   ├── embeddings.py           real neural embeddings
│   └── discover.py             internet discovery + query variation
├── database/
│   ├── \_\_init\_\_.py
│   ├── resource\_store.py       catalog gatekeeper, lazy load + cache
│   ├── persistence.py          THE only module that talks to Postgres
│   ├── create\_table.py         resources table (DESTRUCTIVE — drops first)
│   ├── create\_history\_table.py recommendation\_history (safe, create-only)
│   ├── create\_analysis\_table.py resource\_analysis (safe, create-only)
│   └── add\_verification\_columns.py  migration: adds re-verification tracking
├── verification/
│   ├── \_\_init\_\_.py
│   ├── verifier.py             three gates, parallel network checks
│   └── domain\_policy.py        blocklist / trustlist
├── recommendation/
│   ├── \_\_init\_\_.py
│   ├── scorer.py               100-point arithmetic + confidence
│   └── engine.py               ranking
├── explanation/
│   ├── \_\_init\_\_.py
│   └── decision.py             structured decision records
└── analysis/
    ├── \_\_init\_\_.py
    ├── resource\_analyzer.py          difficulty/format inference (no LLM)
    ├── video\_content\_analyzer.py     YouTube transcript → Gemini chapters
    └── article\_content\_analyzer.py   article/PDF text → Gemini sections
```
Deleted during cleanup: `analysis/test\_connection.py` and
`retrieval/test\_retrieval.py` — untracked scratch files, both stale. The second
used the full repo import path (`from src.agents.recommendation\_system...`)
which never worked from the project's actual run location. Component tests now
live in `if \_\_name\_\_ == "\_\_main\_\_":` blocks inside the modules they test, so
they cannot drift out of sync with the code.
---
9. Running the project
Environment variables
Never hardcoded in any file.
```powershell
$env:DB\_HOST     = "aws-0-<region>.pooler.supabase.com"
$env:DB\_USER     = "postgres.<project-ref>"
$env:DB\_PORT     = "5432"
$env:DB\_NAME     = "postgres"
$env:DB\_PASSWORD = "..."
$env:GEMINI\_API\_KEY = "..."
```
Set these permanently through Windows System Properties rather than with
`$env:` per-window — they are otherwise lost every time a terminal closes.
Connection uses five separate arguments, not one combined URL string,
because the real password contains `@`, `\[`, and `]`, which break URL parsing.
Import rules
The project must be run from inside the `recommendation\_system` folder.
What you are running	Command
Top-level file	`py main.py`, `py orchestrator\_interface.py`, `py reverify.py`
Subfolder file that imports from the project	`py -m database.persistence`
Subfolder file with no project imports	`py database\\create\_table.py`
The `-m` form matters. Running `py database\\persistence.py` puts the script's
folder on the import path, so `from models.resource import ...` fails. The
`-m` form puts the current working directory on the path instead.
First-time setup
```
py database\\create\_table.py
py database\\create\_history\_table.py
py database\\create\_analysis\_table.py
py database\\add\_verification\_columns.py
```
Order matters: the history table's foreign key requires `resources` to exist.
`create\_table.py` is destructive. It runs `DROP TABLE IF EXISTS resources CASCADE`, which also drops `recommendation\_history`. After a reset, re-run
`create\_history\_table.py`.
Routine operation
```
py main.py                    # pipeline test: reproducibility + exclusion
py orchestrator\_interface.py  # integration test: all intents
py reverify.py --dry-run      # audit preview, writes nothing
py reverify.py                # audit for real
```
`reverify.py` should run on a schedule (weekly is reasonable), never during a
recommendation request — a learner should not wait while the catalog is audited.
Note the `\_\_main\_\_` block passes `max\_age\_days=0` to force everything due, which
is right for testing and wrong for scheduled use; call `reverify\_catalog()` with
the default 30 days there.
---
10. Real bugs hit and fixed
A learning record. Each of these was a genuine failure during development.
Environment and tooling
Windows case-sensitivity vs Python imports. Folders named `Twin` and
`DataBase` caused `ModuleNotFoundError` even though Windows treats the names as
equivalent. Fixed with a two-step rename (`Rename-Item Twin twin\_temp`, then
`twin\_temp twin`), since PowerShell refuses a direct case-only rename.
`ModuleNotFoundError` running subfolder scripts. `py database\\persistence.py`
puts the wrong folder on the import path. Fixed by running `py -m database.persistence`. Not a code bug — a launch-method bug.
Missing files that the notes claimed existed. `Resource.from\_dict()` and the
entire `analysis/resource\_analyzer.py` (plus `analysis/\_\_init\_\_.py`) were
documented but not on disk. Documentation drifted from reality; verify against
the filesystem, not the notes.
TLS interception on a restricted network. On some networks (university or
corporate proxy, VPN, antivirus HTTPS scanning) all HTTPS fails with
`CERTIFICATE\_VERIFY\_FAILED` or `invalid peer certificate: UnknownIssuer`, and
DNS fails to resolve. Not a code bug. Fix: use an unrestricted network, or set
`REQUESTS\_CA\_BUNDLE` to the organization's root certificate. Never disable
certificate verification — for a system whose purpose is verifying resources,
that is the wrong trade.
Supabase IPv6 connection timeout. The direct host
(`db.<ref>.supabase.co`) resolves to IPv6 only, which many networks cannot
route — `Connection timed out`, distinct from the DNS failure above. Fixed by
switching to the session pooler host (`aws-0-<region>.pooler.supabase.com`)
with username `postgres.<project-ref>`. Environment variables only, no code
changes — the payoff for never hardcoding connection details.
Newline inside an environment variable. Pressing Enter after the opening
quote in PowerShell stores a leading newline in the value, producing
`user not found in the database` even though the username looks correct. Set
`$env:` values on one line; verify with `$env:DB\_USER` before debugging further.
Correctness
Wikipedia 403 Forbidden. `requests`' default User-Agent looks bot-like and
gets blocked. Fixed by sending a browser-like `User-Agent` header.
Keyword false positive. A naive substring check made `"intro"` match inside
`"introducing"`, mislabelling an advanced paper as beginner. Fixed with
`re.search` and `\\b` word boundaries.
Format assumed rather than verified. (Significant.) `discover.py` set
`format=requested\_format` — "we searched for videos, so this is a video."
Every discovered resource then collected 30 unearned scoring points. Real
examples that falsely claimed to be videos: a YouTube playlist, a TikTok
discovery page, two Microsoft Learn pages, a GeeksforGeeks category listing.
Fixed by setting `format=None` at discovery and inferring conservatively from
the URL, with YouTube path inspection to distinguish a single video from a
playlist or channel. Scores correctly dropped from 80 to 50 for resources whose
format is genuinely unknown.
Discovery counted candidates, not survivors. `MAX\_DISCOVERY\_RESULTS = 5`
stopped after 5 candidates; verification then rejected 4, leaving the learner
with a single recommendation. Fixed by searching in rounds until enough
resources survive verification.
Discarding verified surplus. `verified\_total\[:target]` threw away resources
that had already cost a real HTTP request each, forcing rediscovery later. Fixed
by saving everything verified and returning only `target`. The surplus becomes
shared catalog stock for future requests from any learner.
Duplicate resource entries. After adding real YouTube URLs, the old
Wikipedia-URL versions of the same titles were left in the database; since they
scored identically, the broken old entry kept winning the sort. Fixed by
deleting the duplicates, and prevented permanently by the `UNIQUE` constraint.
Dependencies
`gemini-2.5-flash` deprecated — 404 "no longer available to new users".
Switched to `gemini-3.5-flash`. Gemini model names change often; verify at
https://aistudio.google.com if this errors again.
`google.genai` import error — the library had been uninstalled between
steps. Reinstalled `google-genai` (the current SDK; not the deprecated
`google.generativeai`).
`ddgs` package rename — the once-standard `duckduckgo\_search` was renamed to
`ddgs`; the old import fails on a fresh install.
Supabase connection string parsing — the password's `@`, `\[`, and `]`
characters broke parsing when embedded in one combined URL. Fixed by connecting
with separate arguments.
Security note
One real API key was accidentally pasted into a chat during development and was
revoked and regenerated. Check that Team Alpha's knowledge graph file does
not contain a hardcoded key — it has a line assigning `GOOGLE\_API\_KEY`
directly in code. If a real key was ever committed, it remains in git history
even after deletion.
---
11. Known limitations
Honest list. None of these are hidden; several are deliberate trade-offs.
Duration is never inferred. Nothing in the pipeline determines whether a
resource is short, medium, or long. Every discovered resource therefore
forfeits 20 of 100 points automatically, capping realistic scores at 80. Fixing
this would mean reading YouTube video length or estimating article reading time.
Score ties are broken arbitrarily. Multiple resources routinely score 80.
Python's sort is stable, so the winner is whichever came out of Postgres first
(insertion order), not merit. The learner sees "#1" as the best match when the
system has no actual opinion between several. A tiebreaker signal — known
duration, trusted domain, closer title match — would fix this.
No quality signal in scoring. A pirate site matching all four factors would
outrank Google's crash course matching three. The domain blocklist keeps the
worst offenders out, but quality is not a scoring factor. `TRUSTED\_DOMAINS`
exists and is unused by the scorer — wiring it in is a natural next step.
The blocklist uses substring matching. `if domain in url` would also match
`notreddit.com.example.org`. Fine for filtering search results, insufficient
against a determined bad actor. The proper fix is `urllib.parse.urlparse(url).netloc`.
Blocklist maintenance is ongoing. New junk domains appear continuously — a
video-scraper site (`microtran.org`) entered the catalog after the blocklist was
written. This is a list that needs periodic curation, not a one-time fix.
Extraction from prose is not fully reproducible. The same briefing may
occasionally yield a different level or format. The recommendation decision
remains 100% deterministic given a learner state; it is the extraction step
that is not. Also untested against a real `Evidence.content` string — only
against a hand-written sample. If real briefing phrasing differs, extraction may
return `None` and the learner silently loses points with no error. Caching
extractions by briefing text would close both gaps and is not yet built.
Cached analyses never expire. If a video is re-uploaded or an article
rewritten, stale chapters are served indefinitely. `analyzed\_at` exists so a
staleness policy can be added.
Deleting a resource erases learner history for it. `ON DELETE CASCADE`
means a rejection disappears when a resource is dropped. If the resource is
later rediscovered, a learner who rejected it could see it again.
Degraded mode is non-deterministic. When Postgres is unreachable, discovery
adds to the in-memory cache mid-run, so later requests in the same session see
a different catalog than earlier ones. Observed in a real run where two
identical requests returned different results.
Tiers stop at the first non-empty result, even if weak. After exclusion, a
learner received three resources all scoring 20 with `level 0`, because tier 2
found something and stopped rather than falling through to fresh discovery. At
some point "you have exhausted good beginner material on this topic" may be a
better answer than nine weak matches.
Books are out of scope — by deliberate team decision. Most books are
copyrighted or paywalled with no legitimate full-text access; rather than build
something misleading, book-format resources get an honest "not yet supported"
message.
Re-verification counts consecutive failures only. A resource failing
intermittently never accumulates five strikes. That is the intent — a link that
usually works is not dying — but a flaky resource stays in the catalog forever.
---
12. External dependencies
Library	Purpose	Notes
`psycopg2-binary`	PostgreSQL connectivity	
`sentence-transformers`	Neural embeddings (`all-MiniLM-L6-v2`)	Runs locally after one-time download
`ddgs`	Internet search	Not the old `duckduckgo\_search`
`requests`	HTTP verification and page fetching	Needs a browser-like User-Agent
`youtube-transcript-api`	YouTube transcripts	Unofficial; can be rate-limited
`google-genai`	Gemini API	Not the deprecated `google.generativeai`
`beautifulsoup4`	HTML parsing	
`pypdf`	PDF text extraction	
`networkx`	Knowledge graph (Team Alpha)	Not yet integrated
Supabase was chosen over a local database server because the team wants real
outside-user testing eventually, which requires a server reachable over the
internet by multiple simultaneous users.
---
13. Team Alpha interfaces (as observed)
Useful context for integration. These are their files, not this component's.
`StudentTwin` (`src/twin/student.py`) — the aggregate learner model.
Relevant facts:
`twin\_id: UUID` — the learner identity this engine keys history on.
`model\_config = ConfigDict(extra="forbid")` — fields cannot be added; the
schema is deliberately locked.
`goals: dict\[UUID, Goal]`, and likewise for preferences, knowledge, skills,
interests — dictionaries of objects, not strings.
Their docstring states: "Historical interactions are stored separately by the
Memory System" and "Only the Twin Updater is responsible for modifying the
Twin."
The shape mismatch is the main integration risk. This engine expects
`"goal": "machine learning"` — one string. Their Twin has many `Goal` objects
keyed by UUID. Someone must bridge this, and it should be agreed before
integration rather than discovered during it.
`Memory` (`src/twin/memory.py`) — immutable evidence for the Twin Updater.
Notably it has no `twin\_id` and no structured fields — evidence lives in
a free-text `content: str`. It therefore cannot serve as the recommendation
history store; recovering a URL would mean parsing English. Hence this engine
owns `recommendation\_history` directly.
Future integration point: when a learner rejects resources, that is real
evidence about their preferences. The engine could emit a `Memory` so the Twin
Updater can interpret it — perhaps the learner does not actually want videos, or
the level is wrong. The history table drives filtering; a Memory would carry
the signal upstream. Two separate jobs, neither pretending to be the other.
`ContextBuilder` (`src/retrieval/context\_builder.py`) — formats Evidence
into the prose briefing. Sections are emitted in a hardcoded fixed order:
`STUDENT PROFILE \& TWIN`, then `RELEVANT MEMORIES`, then `RELEVANT KNOWLEDGE`.
This is why front-truncation in the context extractor is safe.
It dumps `item.content` verbatim, so the briefing's structure is fixed but its
wording depends entirely on whoever builds the Evidence objects.
Knowledge graph — a `networkx` DiGraph. Nodes are concepts identified by
name, holding a `Knowledge` object plus an embedding. Edges are prerequisites,
directed from prerequisite to dependent, so `predecessors()` gives what must be
learned first and `successors()` gives what a concept unlocks. Deduplication
uses cosine similarity (≥0.95 reuse, ≥0.85 ask an LLM, else create).
Three blockers for using it:
The graph is in-memory and not persisted — empty at import, gone at exit.
`mastery` is hardcoded to 0 at creation and never updated.
`nx.draw\_spring(G)` and `mtl.show()` run at module level, so importing
the file opens a blocking matplotlib window.
The likely better route is via `EvidenceSource.GRAPH`, which already flows
into the briefing as a `RELEVANT KNOWLEDGE` section — requiring only a prompt
change in the context extractor rather than coupling to an in-memory graph this
component does not control.
---
14. Questions outstanding for the team
For the Orchestrator builder:
What shape is `learner\_state`? Their Twin has `goals: dict\[UUID, Goal]`; this
engine expects one string. Who flattens it?
Should a rejection also create a `Memory`, so the Twin Updater can learn from
it? Who builds that?
Confirm the LLM (not a keyword list) will set `exclude\_seen`.
For the Digital Twin / graph owner:
Where do the `Evidence.content` strings for the TWIN section come from, and
is their wording stable? If those fields could appear as consistent lines
like `Level: beginner`, extraction could be done deterministically with no
LLM call at all — faster, free, fully reproducible, and no Gemini
dependency on the primary path. This would materially strengthen the
research claim.
Is the knowledge graph persisted anywhere, or rebuilt each run?
Does anything populate `mastery`, or is it always 0?
Is `EvidenceSource.GRAPH` evidence already populated, and what does it
contain?
Can the matplotlib lines move into a `\_\_main\_\_` block so the module is
importable?
---
15. Suggested next steps
Immediate:
Send the Orchestrator builder the contract in Section 7. They are
currently building against a stale single-intent interface.
Test context extraction against a real briefing, not the hand-written
sample. Five-minute check that either confirms it works or reveals a gap.
Check for a hardcoded API key in the knowledge graph file, including git
history.
Short-term, roughly in value order:
Cache context extractions by briefing text — closes the reproducibility
gap on the primary path and removes duplicate Gemini calls.
Infer duration (YouTube video length, article reading time) — recovers
20 points currently lost on every resource.
Wire `TRUSTED\_DOMAINS` into scoring as a quality signal, and use it as a
tiebreaker for the many resources scoring identically.
Add a bulk-quality pass to the blocklist — new junk domains keep
appearing.
Longer-term:
Real Digital Twin integration (blocked on the shape question).
Knowledge graph integration (blocked on persistence and mastery).
Staleness policy for cached analyses.
Reconsider whether tiers should fall through when matches are weak, not just
when they are absent.
---
16. Design principles worth preserving
Extracted from decisions that proved correct in practice. If this project is
continued, these are the rules that kept it honest:
Never claim what you have not verified. The format bug awarded 30 points for
an assumption. Every field is either known and correct, or `None`. `None` scores
zero, which is the honest outcome.
Make invalid states structurally impossible. The composite primary key means
a learner cannot be both "shown" and "rejected" for one resource. The `UNIQUE`
constraint means duplicates cannot accumulate. Rules enforced by the database
survive buggy code, other people's scripts, and manual edits.
Degrade honestly, never crash. Every external dependency has a fallback that
prints why: neural embeddings → bag-of-words, Postgres → in-memory, Gemini →
"not supported" status, search failure → empty list. This was validated twice by
total network and database outages during development; the engine kept working
and said exactly what was wrong.
Cheapest checks first. Structural and blocklist checks run before any
network request. Cache lookups run before any API call.
Pay once, share the result. Verified resources and content analyses go into
shared tables. Work done for one learner benefits every learner.
Reproducibility is a feature. Same input, same output — so a recommendation
can be explained, audited, and defended. Variety is available on request, not by
accident.
Documentation drifts; the filesystem does not. Two files this project's own
notes claimed existed were not on disk. Verify before trusting.
