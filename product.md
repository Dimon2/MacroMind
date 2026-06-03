# Product Specification ù MacroMind

## 1) Product goal

Build a **personal macro & risk knowledge base** with grounded AI on top.

Users collect curated market facts in Postgres; the system computes **macro state** from a features ? regime engine pipeline and answers questions using only retrieved context (series, dates, prediction-market probabilities, state). Briefs and alerts are optional outputs from the same store ù not a separate product category.

The product is not a generic chatbot.  
Core pipeline: **ingest ? features ? regime engine ? state service ? Brief / API / UI / Chat** (see [ù16](#16-architecture--delivery-order)).

Deterministic macro state and daily brief are first-class outputs; chat is a later, non-deterministic layer on the same knowledge base.

## 2) Problem statement

Market participants spend too much time stitching together fragmented signals from many sources (macro releases, liquidity data, sentiment, prediction markets, filings).  
Most tools either:

- provide raw charts without interpretation, or
- provide generic AI commentary without verifiable ties to the user's data.

MacroMind combines a curated indicator set, persisted facts, a transparent **features ? regime engine ? macro state** pipeline, and LLM synthesis **only over retrieved context** (chat, later).

## 3) Target users (ICP)

Primary ICP (MVP):

- discretionary macro traders,
- active swing investors,
- independent analysts on a 1-day to multi-week horizon.

User jobs-to-be-done:

- Ask: "What is happening with US liquidity / risk / rates right now?" and get a cited answer.
- Quickly see what changed since yesterday (macro state snapshots + deltas).
- Reduce tab sprawl (FRED, VIX, Kalshi, etc.) into one grounded workspace.

## 4) Core value proposition

- **Your** knowledge base ? not the open internet.
- Transparent **macro state** (regime labels, scores, drivers) that compress facts for retrieval and UI.
- Grounded LLM answers with mandatory source references (series id, observation date, platform).
- One operational view: charts where needed, chat where synthesis helps.

## 5) Scope

### MVP

1. Data ingestion and normalization (FRED, Kalshi, yfinance; more sources later).
2. **Features layer** + **regime engine** ? **`MacroState`** (risk, liquidity, inflation, growth + overlays).
3. **`macro_state_snapshots`** table + CLI **`--update-state`** for day-over-day deltas.
4. **Deterministic daily brief** from state service (template; `--brief-today`).
5. Structured retrieval from Postgres by topic/category (foundation for later chat).

**MVP gate:** at least one end-to-end scenario works reliably (e.g. US liquidity **brief** or cited answer from live DB).

**Explicitly not in MVP:** embeddings, pgvector, chunking, document RAG, non-deterministic chat as primary deliverable.

### v1

1. **State service** ù orchestrates features ? regime engine ? `MacroState`; shared by brief, API, UI.
2. **`macro_state_snapshots`** ù one persisted JSON payload per day (replaces legacy flat `signal_snapshots`).
3. **Deterministic daily brief** + selective alerts (template-first; LLM polish optional and separate).
4. **Deterministic Macro State API** when needed for UI, hosting, or integrations (wraps state service; not a separate pipeline).
5. **UI** ù first-class product surface: state, what changed, brief; charts as support (not a chart-terminal primary).
6. **Grounded chat** ù after brief/UI trust; LLM over retrieved context only.
7. pgvector embeddings for notes and unstructured documents (only when unstructured sources matter).

### Out of scope (early)

- Automated trading execution.
- Portfolio optimization and tax tooling.
- Full media NLP firehose.
- Enterprise compliance workflows.

## 6) Data model and sources (v1 shortlist)

Start with a minimal, high-signal set:

- **Rates/Macro**: US10Y (`DGS10`), US2Y (`DGS2`), 2s10s (`T10Y2Y`), CPI (`CPIAUCSL`), unemployment (`UNRATE`)
- **Liquidity**: TGA, RRP, Fed balance sheet (`WALCL`), M2 (`M2SL`)
- **Risk/Sentiment**: VIX, HY spread (`BAMLH0A0HYM2`), Fear & Greed
- **Prediction overlay**: Polymarket/Kalshi key macro event probabilities
- **Backlog**: insiders / EDGAR, additional PM platforms

## 7) Key features

### A. State service (core)

- Orchestrates: **observations ? `FeatureSet` ? regime engine ? `MacroState` ? public dict** (brief / API / UI).
- Same output drives brief, API, and UI ù no duplicated pipelines.
- Read path: **`--state`** (live compute, no DB write). Persist path: **`--update-state`**.

### B. Features layer

- **`Feature`** ù one standardized metric (e.g. `WALCL_wow_pct`, `RRP_z`, `CPI_yoy`); no regime labels.
- **`FeatureSet`** ù all features at `as_of`, computed from persisted observations (not stored in DB on v1).
- Features are **inputs** to the regime engine, not the user-facing product.

### C. Regime engine

- **`RegimeState`** ù one dimension (risk | liquidity | inflation | growth): label, score, drivers, confidence heuristic.
- **`MacroState`** ù aggregate: all `RegimeState` slices + overlays (curve, PM inflation) + optional composite label.
- Deterministic weighted rules (v1); not ML; `score` / `confidence` are heuristics (ù15).

### D. Daily brief & alerts (first human deliverable)

- **Deterministic** template over live `MacroState` + **deltas from `macro_state_snapshots`** (no LLM required for v1).
- CLI: **`--brief-today`**. Optional LLM polish later ù never the sole source of numbers.
- Low-frequency alerts on regime transitions.

### E. Macro State API (deterministic)

- HTTP JSON wrapper over the state service when external clients need it (UI, hosted SaaS, integrations).
- Core endpoints (v1 target): `/health`, `/state`, `/changes`, `/explain` ù all **deterministic** (same DB ? same response).
- Responses align with `--state` output: `schema_version`, `deterministic: true`, coverage/skipped dimensions.

### F. UI (first-class product surface)

- **Not** a secondary or optional appendix ù a primary way to read state, changes, and the daily brief.
- **Center:** market state, day-over-day deltas, rendered brief ù not a grid of raw indicators.
- **Support:** timeseries for watchlist indicators where context helps.
- Build order: after state service + brief; **product importance** equals brief (different format, same core).
- See [ù15 Product positioning](#15-product-positioning-honest-contract) for what the UI is (and is not) optimizing for.

### G. Grounded Q&A / chat (later)

- Natural-language questions (liquidity, risk, rates, inflation implied by PM).
- Retrieval: SQL by watchlist category + latest observations + current `MacroState`.
- **Non-deterministic** LLM layer; cite every numeric claim; ship after brief/UI establish trust.

## 8) UX principles

- Clarity over complexity.
- Show "what changed" before "everything."
- Every AI claim must trace to a stored fact, feature, or regime driver.
- Say "insufficient data" when the DB is empty or stale.

## 9) Technical approach

### Compute pipeline

```
macro_observations (Postgres)
        ?
features.compute()  ?  FeatureSet
        ?
regime.engine()     ?  MacroState (RegimeState slices + overlays)
        ?
state.mapper()      ?  public dict (schema_version, regimes, ù)
        ?
Brief / API / UI
```

### Storage

- **`macro_observations`** ù raw normalized series (FRED, yfinance, PM).
- **`macro_state_snapshots`** ù one row per `snapshot_date`, JSON **`MacroState`** payload (for deltas + history).
- **Features** ù computed on read from observations in v1 (optional feature snapshots later).

### CLI (target)

| Command | DB write | Purpose |
|---------|----------|---------|
| `--state` | No | Live deterministic `MacroState` JSON |
| `--update-state` | Yes | Upsert today's row in `macro_state_snapshots` |
| `--brief-today` | No | Markdown brief: live state + snapshot deltas |

**Deprecated (remove after migration):** `--signals` ? `--state`; `--snapshot-signals` ? `--update-state`.

**Daily cron:**

```text
--persist-all ? --update-state ? --brief-today
```

### Stack

- **Ingestion**: scheduled crawlers ? Postgres (FRED, Kalshi, yfinance)
- **Brief**: template renderer over state service (CLI/cron first; no HTTP required)
- **API**: FastAPI deterministic endpoints wrapping state service when convenient
- **Cache**: Redis (optional)
- **Frontend**: React UI ù state + changes + brief first; chat later (v1)
- **LLM**: Claude/GPT over retrieved context only for chat; **not** in deterministic brief/state path

## 10) Reliability and quality requirements

- Data freshness per source (last successful fetch, lag).
- Ingestion retries and source-level error visibility.
- Graceful degradation when a source is down.

## 11) Metrics and success criteria

### Product metrics

- Grounded Q&A success rate (user rates answer useful / not).
- WAU among pilots; return frequency.
- Brief/alert engagement (v1).

### MVP gate

- At least one end-to-end scenario works reliably (e.g. US liquidity question answered via **deterministic brief** or later grounded chat from live DB).

### Commercial validation (go/no-go)

Within 6?8 weeks of pilot:

- 10?20 active users,
- 3?5 willing to pay,
- repeat usage ? 3 sessions/week for core cohort.

## 12) Risks and mitigations

- **Risk**: "ChatGPT + CSV" perception.  
  **Mitigation**: Curation, signals, freshness, citations, personal KB.

- **Risk**: Weak data moat (public APIs).  
  **Mitigation**: Workflow, watchlist, regime engine, retention via macro state history and deltas.

- **Risk**: LLM hallucination.  
  **Mitigation**: Retrieval-only prompts; forbid numbers not in context.

- **Risk**: Source fragility.  
  **Mitigation**: Official APIs first; isolated crawlers; monitoring.

- **Risk**: Overpromising predictive regime / trade edge.  
  **Mitigation**: Position as interpreter + KB (ù15); no validated forward claims in product copy; flag low confidence and conflicting drivers in brief/Q&A.

## 13) Delivery plan (first 4 weeks)

Aligned with [ù16](#16-architecture--delivery-order): **features + regime engine ? state service ? Brief ? API (when needed) ? UI ? Chat**.

### Week 1

- Stable ingestion (FRED + PM + market) and DB freshness checks.

### Week 2

- Domain models: `Feature`, `FeatureSet`, `RegimeState`, `MacroState`.
- **Features layer** + **regime engine** (liquidity first, then all dimensions; parity tests vs legacy calculators).
- State service + **`--state`**.

### Week 3

- Migration: **`macro_state_snapshots`**; **`--update-state`**; delta diff from snapshot payloads.
- **Deterministic brief** (`--brief-today`); remove legacy `signal_snapshots` / calculators when parity green.
- Macro State API when UI or hosting needs HTTP ù otherwise defer.

### Week 4

- **UI** v0: state + changes + brief (charts secondary).
- Pilot feedback; grounded chat deferred (embeddings deferred to v1+).

## 14) Non-goals

- Competing with Bloomberg Terminal breadth.
- Universal financial assistant.
- Optimizing for every segment in MVP.
- Predictive macro timing, validated regime alpha, or investment advice (see ù15).

## 15) Product positioning (honest contract)

This section records what MacroMind **is** and **is not**, so delivery stays aligned with a real product ? not a resume demo or a black-box "regime engine."

### What MacroMind is

A **personal macro & risk knowledge base** with a transparent **interpretation layer**:

**curated facts ? features ? regime engine ? macro state ? daily deltas ? grounded brief / Q&A with citations.**

Core question we answer:

> **"What does *my* watchlist show, what changed, and how does our rule-set read it?"**

Primary value is **cognitive offload**: less tab sprawl, consistent vocabulary (risk / liquidity / inflation / growth), personal data memory, and answers you can verify ? not oracle-style market calls.

### What MacroMind is not

- **Not** a Bloomberg-style chart terminal ? indicator UI alone is commodity.
- **Not** a predictive "regime engine" or macro timing system with validated alpha.
- **Not** investment advice, portfolio optimization, trade recommendations, or execution.

Users may draw their own trading conclusions. We do **not** sell validated forward edge or imply the system "knows" what to do with positions.

### Regime engine (replacing legacy calculators)

- **`Feature` / `FeatureSet`** ù standardized metrics from observations (WoW, YoY, z-scores where needed).
- **`RegimeState`** ù per-dimension output: label, score, **`RegimeDriver`** list, confidence heuristic.
- **`MacroState`** ù full snapshot: four regimes + overlays (curve, PM inflation) + optional composite label string.
- Legacy **`signals/calculators.py`** and flat **`signal_snapshots`** are **deprecated**; migrate to engine + **`macro_state_snapshots`**.
- Not a validated inference model or predictive alpha (ù15).

### Near-term delivery priority

**State service ? deterministic Brief ? API (when convenient) ? UI ? Chat** ù not chart-terminal work first.

Build order is not product hierarchy: **UI is first-class** alongside brief; both consume the same state service. Chat comes last.

Brief (and UI) should emphasize:

- what changed (regime score/label deltas from **`macro_state_snapshots`**),
- current regime labels and cited drivers,
- conflicts and **low-confidence** reads where sub-signals disagree,

and should **not** emit price forecasts or exposure recommendations unless explicitly validated later.

### UI principle

UI is a **primary reading surface**, not a secondary API client. Charts support context. The center is **state + change + brief**, not another VIX/WALCL/CPI dashboard.

### Future improvements (evidence-gated)

Optional backlog ù ship with documented limitations only:

- persisted **feature snapshots** (audit / backtest; optional),
- cross-regime interaction flags (e.g. risk-on + tight liquidity),
- simple historical sanity checks before any predictive language in copy.

**Predictive claims** (cycle phase, asset tilts, shock probabilities with implied edge) require out-of-sample validation before they appear in product messaging or brief templates.

### Why this can matter beyond a portfolio project

Interesting products in this space often fail by selling **illusion of edge** without validation. MacroMind's bet is the opposite: **trustworthy, cited macro memory and interpretation** for discretionary operators who already make their own trade calls ù workflow and honesty as retention, not fake alpha.

Architectural choices (state service, deterministic API, brief-first) improve **shipping, trust, and workflow** ù they do **not** by themselves create data or predictive moat (see ù16).

## 16) Architecture & delivery order

### Pipeline

```
ingest ? features ? regime engine ? state service ? Brief ? API (when convenient) ? UI ? Chat
```

- **Ingest:** crawlers persist normalized observations and PM snapshots (`macro_observations`).
- **Features:** `FeatureSet` from observations ù standardized metrics, no labels (computed on read in v1).
- **Regime engine:** `FeatureSet` ? `MacroState` (`RegimeState` per dimension + overlays); deterministic rules + driver weights.
- **State service:** `build_macro_state()`, `build_macro_changes()`, `build_macro_explain()`; maps `MacroState` to public dict.
- **Brief:** first human deliverable; `--brief-today` (live state + snapshot deltas).
- **API:** same public dict over HTTP when needed; not required before brief.
- **UI:** first-class surface (state + changes + brief).
- **Chat:** non-deterministic LLM last.

### Domain model

| Type | Role |
|------|------|
| **`Feature`** | One metric (`WALCL_wow_pct`, `VIX_level`, ù) |
| **`FeatureSet`** | All features at `as_of` |
| **`RegimeDriver`** | Explain row: series, value/z, weight, direction |
| **`RegimeState`** | One regime slice: label, score, drivers, confidence |
| **`MacroState`** | Full snapshot: `regimes`, `overlays`, `composite_label`, coverage |

### Persistence: `macro_state_snapshots`

Replaces legacy flat **`signal_snapshots`** (one row per signal per day).

```text
snapshot_date   DATE PRIMARY KEY
schema_version  TEXT
as_of           TIMESTAMPTZ
status          TEXT          -- computed | partial
payload         JSONB         -- full public MacroState dict
```

- **`--update-state`:** compute `MacroState` ? upsert today's row.
- **Deltas / brief "what changed":** diff consecutive snapshot payloads (e.g. 24h).
- **Brief body (today):** live **`--state`** (fresh after ingest); deltas from snapshots.

Features are **not** persisted in v1 (optional `feature_snapshots` backlog).

### CLI contract

| Command | Writes DB | Output |
|---------|-----------|--------|
| `--state` | No | Live `MacroState` JSON |
| `--update-state` | Yes | Upsert `macro_state_snapshots` + summary |
| `--brief-today` | No | Deterministic markdown |

Deprecated: `--signals` ? `--state`; `--snapshot-signals` ? `--update-state`.

### Deterministic vs non-deterministic

| Layer | Deterministic? | Notes |
|-------|----------------|-------|
| Features + regime engine | Yes | Same observations ? same `MacroState` |
| `--state` / `--update-state` | Yes | Persisted payload is immutable for that date after write |
| Daily brief (v1) | Yes | Template + live state + snapshot deltas |
| `/v1/macro/state`, `/changes`, `/explain`, `/health` | Yes | `deterministic: true`, `schema_version` |
| Chat / `POST /ask` | No | LLM; citations required |
| Brief LLM polish (optional) | No | Never sole source of metrics |

### State service functions

- `build_macro_state()` ? `MacroState` / public dict
- `build_macro_changes(window)` ? regime deltas from `macro_state_snapshots`
- `build_macro_explain(regime)` ? drivers from `RegimeState`

### Macro State API (HTTP, when shipped)

Same payload as `--state`. Example:

```json
{
  "schema_version": "1.0",
  "deterministic": true,
  "as_of": "2026-06-03T21:00:00Z",
  "regimes": {
    "risk": { "value": "risk_on", "score": 0.72, "confidence": 0.64 }
  },
  "delta_24h": { "liquidity": -0.08 }
}
```

`score` / `confidence` are **heuristic** ù not validated probabilities (ù15).

### Code layout (target)

```text
src/macromind/
  features/          # compute FeatureSet
  state/
    engine/          # regime rules per dimension
    service.py       # build_macro_*
    mapper.py        # MacroState ? public dict
  brief/             # template + --brief-today
  db/                # macro_state_snapshots repository
```

Legacy **`signals/calculators.py`** removed after engine parity tests pass.

### Migration PR order (reference)

1. Domain models  
2. Features compute  
3. Regime engine (liquidity ? all dimensions)  
4. State service + mapper  
5. `macro_state_snapshots` + `--state` / `--update-state`  
6. Remove calculators + `signal_snapshots`  
7. `--brief-today`  
8. Macro State API (optional)

### Build order vs product importance

| | Build order | Product importance |
|--|-------------|-------------------|
| Features + regime engine | 1 | Core |
| State service + `--update-state` | 2 | Core |
| Brief | 3 | High |
| API | 4 (when needed) | High for SaaS/integrations |
| UI | 5 | **High** ù equal to brief |
| Chat | 6 | Medium until trust exists |

### Moat expectations

Architecture improves **trust, reproducibility, and workflow** (weak moat: habit, hosted convenience, cited interpreter).

It does **not** add exclusive data or validated predictive alpha. Do not market deterministic scores as forecast edge.
