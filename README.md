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
- `src/ai_market_terminal/models.py` - `DataPoint` contract (macro timeseries)
- `src/ai_market_terminal/prediction_markets/` - Kalshi client, resolver, snapshots
- `src/ai_market_terminal/db/` - Postgres connection, migrations, repository
- `config/kalshi_watchlist.yaml` - allowlisted Kalshi series (US macro)
- `src/ai_market_terminal/crawlers/*` - source crawlers
- `src/ai_market_terminal/runner.py` - crawler registry and orchestration

### Setup (Kalshi + Postgres)

1. Start Postgres (example):

```bash
docker run -d --name postgres \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=market_db \
  -p 5432:5432 pgvector/pgvector:pg17
```

2. Install dependencies and configure env (from repo root):

```powershell
pip install -r requirements.txt
copy .env.example .env
```

3. Apply migrations:

```powershell
$env:PYTHONPATH="src"
python -m ai_market_terminal.db.migrate
```

Or via main: `python main.py --migrate --crawler kalshi`

4. Ingest Kalshi prediction markets:

```powershell
$env:PYTHONPATH="src"
python main.py --crawler kalshi --persist
```

Preview without DB write:

```powershell
python main.py --crawler kalshi
```

5. Verify data in Postgres:

```bash
docker exec -it postgres psql -U admin -d market_db -c "
SELECT s.macro_topic, e.event_ticker, m.outcome_label, o.yes_probability
FROM pm_observations o
JOIN pm_markets m USING (platform, market_ticker)
JOIN pm_events e USING (platform, event_ticker)
JOIN pm_series s ON s.platform = e.platform AND s.series_ticker = e.series_ticker
WHERE o.period_date = CURRENT_DATE
ORDER BY 1, 2;"
```

Run locally (legacy macro crawlers):

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
