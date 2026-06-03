# Product Specification ? MacroMind

## 1) Product goal

Build a **personal macro & risk knowledge base** with grounded AI on top.

Users collect curated market facts in Postgres; the system computes transparent signals and answers questions using only retrieved context (series, dates, prediction-market probabilities, signals). Briefs and alerts are optional outputs from the same store ? not a separate product category.

The product is not a generic chatbot.  
Core pipeline: **ingest ? state service ? Brief / API / UI / Chat** (see [ù16](#16-architecture--delivery-order)).

Deterministic macro state and daily brief are first-class outputs; chat is a later, non-deterministic layer on the same knowledge base.

## 2) Problem statement

Market participants spend too much time stitching together fragmented signals from many sources (macro releases, liquidity data, sentiment, prediction markets, filings).  
Most tools either:

- provide raw charts without interpretation, or
- provide generic AI commentary without verifiable ties to the user's data.

MacroMind combines a curated indicator set, persisted facts, rule-based signals, and LLM synthesis **only over retrieved context**.

## 3) Target users (ICP)

Primary ICP (MVP):

- discretionary macro traders,
- active swing investors,
- independent analysts on a 1-day to multi-week horizon.

User jobs-to-be-done:

- Ask: "What is happening with US liquidity / risk / rates right now?" and get a cited answer.
- Quickly see what changed since yesterday (signals + deltas).
- Reduce tab sprawl (FRED, VIX, Kalshi, etc.) into one grounded workspace.

## 4) Core value proposition

- **Your** knowledge base ? not the open internet.
- Transparent signals that compress facts for retrieval and UI.
- Grounded LLM answers with mandatory source references (series id, observation date, platform).
- One operational view: charts where needed, chat where synthesis helps.

## 5) Scope

### MVP

1. Data ingestion and normalization (FRED, Kalshi, yfinance; more sources later).
2. Rule-based signals feeding a **state service** (risk, liquidity, inflation, growth regimes + deltas).
3. **Deterministic daily brief** from state service (template; CLI/cron acceptable).
4. Structured retrieval from Postgres by topic/category (foundation for later chat).

**MVP gate:** at least one end-to-end scenario works reliably (e.g. US liquidity **brief** or cited answer from live DB).

**Explicitly not in MVP:** embeddings, pgvector, chunking, document RAG, non-deterministic chat as primary deliverable.

### v1

1. **State service** ù single Python core: macro state, changes, explain inputs (shared by brief, API, UI).
2. Signal snapshots and day-over-day deltas (inputs to state service).
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

- Single module builds **macro state**, **changes**, and **explain** payloads from persisted observations and signal snapshots.
- Rule-based, inspectable; signals are inputs to a state function (evolving from v0 calculators).
- Same output drives brief, API, and UI ù no duplicated pipelines.

### B. Daily brief & alerts (first human deliverable)

- **Deterministic** template + state + deltas from the state service (no LLM required for v1).
- Optional LLM polish later ù never the sole source of numbers.
- Low-frequency alerts on regime/signal transitions.

### C. Macro State API (deterministic)

- HTTP JSON wrapper over the state service when external clients need it (UI, hosted SaaS, integrations).
- Core endpoints (v1 target): `/health`, `/state`, `/changes`, `/explain` ù all **deterministic** (same DB ? same response).
- Responses include `schema_version`, `deterministic: true`, coverage/skipped dimensions; scores/confidence are heuristics, not validated probabilities (see ù15).

### D. UI (first-class product surface)

- **Not** a secondary or optional appendix ù a primary way to read state, changes, and the daily brief.
- **Center:** market state, day-over-day deltas, rendered brief ù not a grid of raw indicators.
- **Support:** timeseries for watchlist indicators where context helps.
- Build order: after state service + brief; **product importance** equals brief (different format, same core).
- See [ù15 Product positioning](#15-product-positioning-honest-contract) for what the UI is (and is not) optimizing for.

### E. Signals (v0 ? state inputs)

- Rule-based, inspectable calculators over normalized observations.
- Used as compact facts feeding the state service (not a black box).

### F. Grounded Q&A / chat (later)

- Natural-language questions (liquidity, risk, rates, inflation implied by PM).
- Retrieval: SQL by watchlist category + latest observations + current state/signals.
- **Non-deterministic** LLM layer; cite every numeric claim; ship after brief/UI establish trust.

## 8) UX principles

- Clarity over complexity.
- Show "what changed" before "everything."
- Every AI claim must trace to a stored fact or signal.
- Say "insufficient data" when the DB is empty or stale.

## 9) Technical approach

- **Ingestion**: scheduled crawlers ? Postgres (FRED, Kalshi, yfinance)
- **State service**: Python core (`build_macro_state`, `build_macro_changes`, `build_macro_explain`) ù shared by brief, API, UI
- **Brief**: template renderer over state service (CLI/cron first; no HTTP required)
- **API**: FastAPI deterministic endpoints wrapping state service when convenient (UI hosting, SaaS, integrations)
- **Storage**: Postgres timeseries (relational retrieval on MVP)
- **Cache**: Redis (optional)
- **Frontend**: React UI ù state + changes + brief first; chat later (v1)
- **LLM**: Claude/GPT over retrieved context only for chat; **no embeddings on MVP**; **not** in deterministic brief/state path

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
  **Mitigation**: Workflow, watchlist, signal framework, retention via deltas and history.

- **Risk**: LLM hallucination.  
  **Mitigation**: Retrieval-only prompts; forbid numbers not in context.

- **Risk**: Source fragility.  
  **Mitigation**: Official APIs first; isolated crawlers; monitoring.

- **Risk**: Overpromising predictive regime / trade edge.  
  **Mitigation**: Position as interpreter + KB (?15); no validated forward claims in product copy; flag low confidence and conflicting inputs in brief/Q&A.

## 13) Delivery plan (first 4 weeks)

Aligned with [ù16](#16-architecture--delivery-order): **state service ? Brief ? API (when needed) ? UI ? Chat**.

### Week 1

- Stable ingestion (FRED + PM + market) and DB freshness checks.

### Week 2

- **State service** v1 (wrap existing signals + deltas into stable internal contract).
- **Deterministic brief** (CLI/template) for pilot reading.

### Week 3

- Signal snapshots / delta polish; brief content (what changed, cited inputs, low-confidence flags).
- Macro State API (`/health`, `/state`, `/changes`, `/explain`) when UI or hosting needs HTTP ù otherwise defer.

### Week 4

- **UI** v0: state + changes + brief (charts secondary).
- Pilot feedback; grounded chat deferred until brief/UI trusted (embeddings deferred to v1+).

## 14) Non-goals

- Competing with Bloomberg Terminal breadth.
- Universal financial assistant.
- Optimizing for every segment in MVP.
- Predictive macro timing, validated regime alpha, or investment advice (see ù15).

## 15) Product positioning (honest contract)

This section records what MacroMind **is** and **is not**, so delivery stays aligned with a real product ? not a resume demo or a black-box "regime engine."

### What MacroMind is

A **personal macro & risk knowledge base** with a transparent **interpretation layer**:

**curated facts ? rule-based signals ? daily deltas ? grounded brief / Q&A with citations.**

Core question we answer:

> **"What does *my* watchlist show, what changed, and how does our rule-set read it?"**

Primary value is **cognitive offload**: less tab sprawl, consistent vocabulary (risk / liquidity / inflation / growth), personal data memory, and answers you can verify ? not oracle-style market calls.

### What MacroMind is not

- **Not** a Bloomberg-style chart terminal ? indicator UI alone is commodity.
- **Not** a predictive "regime engine" or macro timing system with validated alpha.
- **Not** investment advice, portfolio optimization, trade recommendations, or execution.

Users may draw their own trading conclusions. We do **not** sell validated forward edge or imply the system "knows" what to do with positions.

### Signals (current generation)

Rule-based, inspectable **v0 telemetry + labels** (`risk_regime`, `liquidity_regime`, `inflation_regime`, `growth_regime`, plus standalone overlays such as curve proxy and PM inflation probability).

- `market_state` is a **composite label** for retrieval and UI ? a string encoding of four dimensions, not a calibrated state machine.
- Known limits (acceptable for v1): limited second-order features, no cross-signal interaction rules yet, no backtested hit rates, heuristic liquidity inputs (e.g. RRP % change without level context).

Signals compress facts for retrieval; they are **not** a validated inference model until evidence says otherwise.

### Near-term delivery priority

**State service ? deterministic Brief ? API (when convenient) ? UI ? Chat** ù not signal sophistication or chart-terminal work first.

Build order is not product hierarchy: **UI is first-class** alongside brief; both consume the same state service. Chat comes last.

Brief (and UI) should emphasize:

- what changed (signal deltas),
- current regime labels and cited inputs,
- conflicts and **low-confidence** reads where sub-signals disagree,

and should **not** emit price forecasts or exposure recommendations unless explicitly validated later.

### UI principle

UI is a **primary reading surface**, not a secondary API client. Charts support context. The center is **state + change + brief**, not another VIX/WALCL/CPI dashboard.

### Future improvements (evidence-gated)

Optional backlog ? ship with documented limitations only:

- second-order features (e.g. VIX change horizons, CPI acceleration, liquidity z-scores),
- regime vector / confidence scores instead of false-precision labels,
- small set of interaction flags (e.g. risk-on + tight liquidity),
- simple historical sanity checks before any predictive language in copy.

**Predictive claims** (cycle phase, asset tilts, shock probabilities with implied edge) require out-of-sample validation before they appear in product messaging or brief templates.

### Why this can matter beyond a portfolio project

Interesting products in this space often fail by selling **illusion of edge** without validation. MacroMind's bet is the opposite: **trustworthy, cited macro memory and interpretation** for discretionary operators who already make their own trade calls ù workflow and honesty as retention, not fake alpha.

Architectural choices (state service, deterministic API, brief-first) improve **shipping, trust, and workflow** ù they do **not** by themselves create data or predictive moat (see ù16).

## 16) Architecture & delivery order

### Pipeline

```
ingest ? state service ? Brief ? API (when convenient) ? UI ? Chat
```

- **Ingest:** crawlers persist normalized observations and PM snapshots.
- **State service:** one Python core produces macro state, 24h (or configurable) changes, and per-regime explain payloads. Brief, API, and UI call this layer ù no duplicate logic.
- **Brief:** first human-facing deliverable; deterministic template over state service (CLI/cron OK before HTTP).
- **API:** JSON wrapper over the same state service when external clients need it (React UI, hosted SaaS, integrations). Not required before brief.
- **UI:** first-class product surface (state + changes + brief); not demoted to "optional client."
- **Chat:** non-deterministic LLM Q&A last; builds on trust established by brief/UI.

### Deterministic vs non-deterministic

| Layer | Deterministic? | Notes |
|-------|------------------|-------|
| State service | Yes | Same DB snapshot ? same output |
| Daily brief (v1) | Yes | Template + state + deltas |
| `/v1/macro/state`, `/changes`, `/explain`, `/health` | Yes | `deterministic: true`, `schema_version` in responses |
| Chat / `POST /ask` | No | LLM; citations required; numbers only from retrieved context |
| Brief LLM polish (optional) | No | Separate artifact; never sole source of metrics |

### State service contract (internal, v1 target)

Functions (names illustrative):

- `build_macro_state()` ù regimes (risk, liquidity, inflation, growth), labels, scores, coverage, `as_of`
- `build_macro_changes(window)` ù deltas, significance, driver series keys
- `build_macro_explain(regime)` ù drivers from cited inputs (weights when feature layer ships)

Evolution: v0 wraps existing `SignalService` + snapshots/deltas; later adds feature layer and weighted regime engine without breaking the external contract.

### Macro State API (HTTP, when shipped)

Primary machine-facing product alongside brief/UI. Example shape:

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

`score` / `confidence` are **heuristic coordinates and agreement signals** ù not validated probabilities or trading edge (ù15).

### Build order vs product importance

| | Build order (what to ship first) | Product importance |
|--|----------------------------------|--------------------|
| State service | 1 | Core |
| Brief | 2 | High |
| API | 3 (when UI/hosting needs it) | High for integrations/SaaS |
| UI | 4 | **High** ù equal to brief as reading experience |
| Chat | 5 | Medium until trust exists |

### Moat expectations

These architecture choices add **trust, reproducibility, and workflow** (weak moat: habit, hosted convenience, cited interpreter).

They do **not** add exclusive data or validated predictive alpha. Do not market deterministic scores as forecast edge.
