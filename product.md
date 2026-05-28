# Product Specification — AI Market Intelligence Terminal

## 1) Product goal

Build a focused market intelligence terminal that helps users make better daily macro/risk decisions through structured signals and concise interpretation.

The product is not a generic chatbot.  
It is a repeatable decision workflow: **data -> regime -> brief -> alert -> action**.

## 2) Problem statement

Market participants spend too much time stitching together fragmented signals from many sources (macro releases, liquidity data, sentiment, prediction markets, filings).  
Most tools either:

- provide raw charts without interpretation, or
- provide generic AI commentary without a strong signal framework.

We solve this by combining selected indicators into a coherent market state model and surfacing only material changes.

## 3) Target users (ICP)

Primary ICP (v1):

- discretionary macro traders,
- active swing investors,
- independent analysts who operate on 1-day to multi-week horizon.

User jobs-to-be-done:

- Quickly answer: "What changed in market regime since yesterday?"
- Detect liquidity/risk stress earlier.
- Reduce noise and avoid information overload.

## 4) Core value proposition

- One operational market view instead of many disconnected tabs.
- Regime-aware interpretation (not just metric snapshots).
- Actionable daily brief and alerts with clear rationale.

## 5) Scope for MVP (v1)

### In scope

1. Data ingestion and normalization for a curated set of indicators.
2. Regime classification (rule-based baseline).
3. Daily brief generation (deterministic template + LLM polish).
4. Alerting on key threshold or regime transitions.
5. Dashboard with trend charts and regime state.

### Out of scope

- Automated trading execution.
- Portfolio optimization and tax tooling.
- Full NLP firehose over all financial media.
- Enterprise compliance workflows.

## 6) Data model and sources (v1 shortlist)

Start with a minimal, high-signal set:

- **Rates/Macro**: US10Y (`DGS10`), US2Y (`DGS2`), 2s10s (`T10Y2Y`), CPI (`CPIAUCSL`), unemployment (`UNRATE`)
- **Liquidity**: TGA, RRP, Fed balance sheet (`WALCL`), M2 (`M2SL`)
- **Risk/Sentiment**: VIX, HY spread (`BAMLH0A0HYM2`), Fear & Greed
- **Prediction overlay**: Polymarket/Kalshi key macro event probabilities

All additional sources from the data-source PDF are backlog until baseline reliability is proven.

## 7) Key features

### A. Daily Market Brief

- Generated once per day (configurable market session).
- Includes:
  - current regime,
  - top 3 state changes vs previous day/week,
  - risk monitor (improving/neutral/deteriorating),
  - watch items for next 24-72h.

### B. Regime Detector

Initial rule-based classifier with transparent logic:

- Growth trend (improving/flat/deteriorating),
- Inflation trend (cooling/sticky/reaccelerating),
- Liquidity impulse (positive/neutral/negative),
- Risk appetite (risk-on/neutral/risk-off).

Combined into a simple market-state label.

### C. Signal Alerts

- Trigger types:
  - threshold breach,
  - regime transition,
  - multi-signal confirmation event.
- Alert quality target: low frequency, high relevance.

### D. Dashboard

- Timeseries charts for v1 indicators.
- Regime panel and current state.
- Brief history feed.

## 8) UX principles

- Clarity over complexity.
- Show "what changed" before "everything."
- Every alert must include reason and source signals.
- Explainability is mandatory for trust.

## 9) Technical approach

- **Backend**: FastAPI with scheduled ingestion jobs
- **Storage**: Postgres timeseries tables
- **Cache**: Redis for fast recent reads
- **Frontend**: React dashboard
- **LLM usage**:
  - summarize structured signals,
  - never fabricate raw data values,
  - attach source timestamps to generated brief blocks.

## 10) Reliability and quality requirements

- Data freshness SLA per source category.
- Ingestion retries + dead-letter logging for failures.
- Source-level observability (last successful fetch, lag, error count).
- Graceful degradation when one source is unavailable.

## 11) Metrics and success criteria

## Product metrics

- WAU/DAU among pilot users.
- Brief open rate.
- Alert interaction rate.
- Weekly retention.

## Quality metrics

- Data ingestion success rate.
- Alert precision proxy (user "useful/not useful" feedback).
- Brief generation success and latency.

## Commercial validation (go/no-go)

Within 6-8 weeks of pilot:

- 10-20 active users,
- at least 3-5 users willing to pay,
- repeat usage >= 3 sessions/week/user for core cohort.

If these are not met, narrow ICP or pivot feature set.

## 12) Risks and mitigations

- **Risk**: Large AI vendors replicate generic features.  
  **Mitigation**: Focus on niche workflow, proprietary signal framework, and execution quality.

- **Risk**: Source instability / scraping fragility.  
  **Mitigation**: Prefer official APIs, isolate fragile connectors, monitor and fallback.

- **Risk**: Signal noise.  
  **Mitigation**: Keep indicator set small, tune thresholds, collect user feedback loops.

## 13) Delivery plan (first 4 weeks)

### Week 1

- Finalize v1 indicators and schema.
- Implement ingestion for core FRED + 1 liquidity source.

### Week 2

- Build dashboard baseline + timeseries endpoints.
- Add data quality monitoring basics.

### Week 3

- Implement regime detector (rule-based).
- Implement daily brief template and history.

### Week 4

- Add alerts and pilot feedback capture.
- Stabilize reliability and iterate on signal quality.

## 14) Non-goals

- Competing with Bloomberg Terminal feature breadth.
- Building a universal assistant for all finance use cases.
- Optimizing for every user segment in v1.
