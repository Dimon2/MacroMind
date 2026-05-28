# AI Market Intelligence Terminal

AI Market Intelligence Terminal is a focused decision-support product for macro and cross-asset market participants.  
It combines macro, liquidity, sentiment, and prediction-market signals into one daily operating view.

## Why this project

General-purpose AI tools are strong at broad explanations, but they are not optimized for repeatable, market-specific workflows.  
This project focuses on:

- curated high-signal market data sources,
- structured regime detection (risk-on/risk-off, liquidity pressure, cycle phase),
- actionable daily outputs (briefs and alerts), not just chat responses.

## Target user (ICP)

Primary ICP for v1:

- discretionary macro traders,
- active swing investors,
- research-driven market operators who want a daily macro/liquidity dashboard with concise interpretation.

## MVP scope (v1)

v1 is intentionally narrow and operational.

Core capabilities:

- ingest and normalize selected data sources (macro, liquidity, sentiment, prediction markets),
- compute regime and stress indicators,
- generate a daily brief with key market state changes,
- trigger a small set of high-value alerts.

Out of scope for v1:

- full-featured portfolio management,
- HFT or intraday execution infrastructure,
- broad social/news scraping at massive scale,
- "general assistant for everything financial."

## Data source groups

Based on project map in `ai_market_terminal_data_sources_en.pdf`.

- Macroeconomic data (FRED, BLS, yfinance proxies)
- Liquidity indicators (TGA, RRP, Fed balance sheet, money supply, credit spreads)
- Market sentiment (Fear & Greed, VIX, surveys, options positioning)
- Prediction markets (Polymarket, Kalshi, PredictIt, FedWatch-style probabilities)
- Insiders and institutional flows (EDGAR, short data, unusual options where feasible)

## Suggested architecture

- **Backend**: FastAPI (ingestion, scheduled jobs, agent orchestration)
- **Database**: Postgres (+ pgvector if/when retrieval is needed)
- **Cache**: Redis/Upstash for near-real-time views
- **Frontend**: React + charting library for dashboard and brief UI
- **AI layer**: LLM-assisted interpretation over structured indicators

## Getting started (project bootstrap)

This repository is currently in planning/bootstrap stage.

Recommended first implementation steps:

1. Build ingestion for 5-7 highest-value indicators only.
2. Create a canonical timeseries schema in Postgres.
3. Implement one regime classifier (simple rules first).
4. Generate one deterministic daily brief (template + metrics).
5. Add one alert channel (in-app + optional Telegram/email).

## Current Python skeleton

Project structure (ingestion-first):

- `main.py` - CLI entry point for running one/all crawlers
- `src/ai_market_terminal/models.py` - `DataPoint` contract
- `src/ai_market_terminal/crawlers/base.py` - crawler interface
- `src/ai_market_terminal/crawlers/*` - phase 1 crawler stubs
- `src/ai_market_terminal/runner.py` - crawler registry and orchestration

Run locally (from repo root):

- PowerShell: `$env:PYTHONPATH="src"; python main.py --crawler all`
- Or one crawler: `$env:PYTHONPATH="src"; python main.py --crawler fred`

## Success criteria for v1

- Daily brief is delivered reliably with meaningful state changes.
- Alerts are low-noise and action-relevant.
- Early users return at least 3x per week.
- At least 3-5 users confirm willingness to pay.

## Roadmap (high level)

- **Phase 1**: Data reliability + baseline dashboard
- **Phase 2**: Regime detection + daily brief
- **Phase 3**: Alerting + personalization by user profile
- **Phase 4**: Validation loop (retention, paid pilots, iteration)

## Project docs

- Product specification: `product.md`
- Data source map: `ai_market_terminal_data_sources_en.pdf`
