# Product Specification ? MacroMind

## 1) Product goal

Build a **personal macro & risk knowledge base** with grounded AI on top.

Users collect curated market facts in Postgres; the system computes transparent signals and answers questions using only retrieved context (series, dates, prediction-market probabilities, signals). Briefs and alerts are optional outputs from the same store ? not a separate product category.

The product is not a generic chatbot.  
Core workflow: **data ? signals ? retrieval ? grounded answer** (brief/alert/UI are layers on the same KB).

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
2. Rule-based signals (risk regime, curve proxy, PM inflation overlay, etc.).
3. Structured retrieval from Postgres by topic/category.
4. Grounded Q&A via LLM over a **structured** context pack (SQL by category/series + signals).

**Explicitly not in MVP:** embeddings, pgvector, chunking, or document RAG.

### v1

1. Signal snapshots and day-over-day deltas.
2. Dashboard UI (charts + chat).
3. pgvector embeddings for notes and unstructured documents (only when unstructured sources matter).
4. Deterministic daily brief + selective alerts (artifacts from KB).

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

### A. Grounded Q&A (MVP centerpiece)

- Natural-language questions (liquidity, risk, rates, inflation implied by PM).
- Retrieval: SQL by watchlist category + latest observations + current signals.
- LLM response constrained to context; cite every numeric claim.

### B. Signals

- Rule-based, inspectable calculators over normalized observations.
- Used as compact facts in retrieval and UI (not a black box).

### C. Daily brief & alerts (v1 polish)

- Template + metrics (+ optional LLM polish) from the same DB.
- Low-frequency alerts on regime/signal transitions.

### D. Dashboard

- **Center:** market state, day-over-day deltas, grounded brief/chat ? not a grid of raw indicators.
- **Support:** timeseries for watchlist indicators where context helps.
- See [?15 Product positioning](#15-product-positioning-honest-contract) for what the UI is (and is not) optimizing for.

## 8) UX principles

- Clarity over complexity.
- Show "what changed" before "everything."
- Every AI claim must trace to a stored fact or signal.
- Say "insufficient data" when the DB is empty or stale.

## 9) Technical approach

- **Backend**: FastAPI with scheduled ingestion and retrieval endpoints
- **Storage**: Postgres timeseries (relational retrieval on MVP)
- **Cache**: Redis (optional)
- **Frontend**: React dashboard + chat (v1)
- **LLM**: Claude/GPT over retrieved context only; **no embeddings on MVP**

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

- At least one end-to-end scenario works reliably (e.g. US liquidity question ? cited answer from live DB).

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

### Week 1

- Stable ingestion (FRED + PM + market) and DB freshness checks.

### Week 2

- Structured retrieval by topic + `--signals` in context pack.
- First grounded Q&A path (CLI or minimal API).

### Week 3

- Signal history / deltas; tighten prompt and citation format.

### Week 4

- Thin API + pilot feedback; plan UI (embeddings deferred to v1).

## 14) Non-goals

- Competing with Bloomberg Terminal breadth.
- Universal financial assistant.
- Optimizing for every segment in MVP.
- Predictive macro timing, validated regime alpha, or investment advice (see §15).

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

**API + daily brief** over signal sophistication.

Brief and chat should emphasize:

- what changed (signal deltas),
- current regime labels and cited inputs,
- conflicts and **low-confidence** reads where sub-signals disagree,

and should **not** emit price forecasts or exposure recommendations unless explicitly validated later.

### UI principle

Charts support context. The product center is **state + change + grounded synthesis**, not another VIX/WALCL/CPI dashboard.

### Future improvements (evidence-gated)

Optional backlog ? ship with documented limitations only:

- second-order features (e.g. VIX change horizons, CPI acceleration, liquidity z-scores),
- regime vector / confidence scores instead of false-precision labels,
- small set of interaction flags (e.g. risk-on + tight liquidity),
- simple historical sanity checks before any predictive language in copy.

**Predictive claims** (cycle phase, asset tilts, shock probabilities with implied edge) require out-of-sample validation before they appear in product messaging or brief templates.

### Why this can matter beyond a portfolio project

Interesting products in this space often fail by selling **illusion of edge** without validation. MacroMind's bet is the opposite: **trustworthy, cited macro memory and interpretation** for discretionary operators who already make their own trade calls ? workflow and honesty as retention, not fake alpha.
