# MacroMind

**Personal macro & risk intelligence — your data, your signals, grounded AI.**

MacroMind is a personal financial knowledge base for macro and cross-asset operators.  
It ingests curated market data into Postgres, computes transparent rule-based signals, and (roadmap) answers questions with an LLM using only what is in your database — with citations, not hallucinated numbers.

> Python package: `macromind` (`src/macromind`). Clone folder / GitHub repo: **MacroMind**.

## Why MacroMind

General-purpose AI is strong at explanations but weak at **your** watchlist, **your** freshness, and **your** signal framework.

MacroMind focuses on:

- curated high-signal sources (macro, liquidity, prediction markets, market proxies),
- structured facts and signals in Postgres,
- grounded Q&A and UI (LLM reads context from the DB),
- optional briefs/alerts as artifacts from the same knowledge base — not a separate product.

## Target user (ICP)

Primary ICP for MVP:

- discretionary macro traders,
- active swing investors,
- research-driven operators who want one place to ask: *"What changed in liquidity / risk since yesterday?"*

## MVP → v1

**MVP (now):**

- ingest and normalize selected sources (FRED, Kalshi, yfinance),
- rule-based signals (`--signals`),
- grounded Q&A: question → **SQL / category retrieval** + signal context → LLM answer with dates and series ids.

**Not in MVP:** embeddings, pgvector, or document RAG — structured timeseries only.

**v1 (later):**

- signal history and deltas,
- dashboard UI + daily brief/alerts from the same store,
- optional pgvector embeddings for notes and unstructured sources.

Out of scope for early versions:

- full portfolio management,
- HFT / execution,
- generic “financial assistant for everything.”

## Data source groups

Based on project map in `macromind_data_sources_en.pdf` (legacy filename `ai_market_terminal_data_sources_en.pdf` if present).

- Macroeconomic data (FRED, BLS, yfinance proxies)
- Liquidity indicators (TGA, RRP, Fed balance sheet, money supply, credit spreads)
- Market sentiment (Fear & Greed, VIX, surveys, options positioning)
- Prediction markets (Polymarket, Kalshi, PredictIt, FedWatch-style probabilities)
- Insiders and institutional flows (EDGAR, short data — backlog)

## Suggested architecture

- **Backend**: FastAPI (ingestion, retrieval, LLM orchestration)
- **Database**: Postgres (plain relational retrieval for MVP)
- **Cache**: Redis/Upstash (optional, for hot reads)
- **Frontend**: React + charts + chat over the same API
- **AI layer**: LLM over structured context only (series + signals + PM); no embeddings on MVP

## Getting started

### Current Python layout

- `main.py` — CLI: crawlers, persist, `--signals`
- `src/macromind/models.py` — `DataPoint` contract
- `src/macromind/prediction_markets/` — Kalshi client, resolver, snapshots
- `src/macromind/macro/` — FRED client and watchlist
- `src/macromind/market/` — yfinance client and watchlist
- `src/macromind/signals/` — rule-based signal calculators
- `src/macromind/db/` — Postgres, migrations, repositories
- `config/*.yaml` — FRED, Kalshi, market watchlists
- `src/macromind/crawlers/*` — source crawlers
- `.cursor/rules/python-venv.mdc` — use `.venv` for Python/pip

### Setup (Kalshi + Postgres)

1. Start Postgres (example):

```bash
docker run -d --name postgres \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=market_db \
  -p 5432:5432 postgres:17
```

MVP uses relational queries only (no pgvector). The `pgvector/pgvector` image is optional for a later v1 if you want embeddings preinstalled.

2. Create venv, install dependencies, and configure env (from repo root):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

3. Apply migrations:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m macromind.db.migrate
```

Migrate only: `.\.venv\Scripts\python.exe main.py --migrate`

Migrate + ingest: `.\.venv\Scripts\python.exe main.py --migrate --crawler kalshi --persist`

4. Ingest Kalshi prediction markets:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe main.py --crawler kalshi --persist
```

Preview without DB write:

```powershell
.\.venv\Scripts\python.exe main.py --crawler kalshi
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

### Setup (FRED macro series)

1. Add `FRED_API_KEY` to `.env` (free key from [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html)).

2. Quick check in the browser (substitute your key for `YOUR_KEY`):

   [FRED API — series UNRATE (JSON)](https://api.stlouisfed.org/fred/series?series_id=UNRATE&api_key=YOUR_KEY&file_type=json)

   - **200** with `"seriess"` in the body — key works.
   - **401** — invalid or missing key.
   - **429** — rate limit / temporary block; wait and retry later.

3. Apply migrations (includes `002_macro_tables.sql`):

```powershell
$env:PYTHONPATH="src"
python -m macromind.db.migrate
```

4. Ingest FRED series from `config/fred_series.yaml`:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe main.py --crawler fred --persist
```

Preview without DB write:

```powershell
.\.venv\Scripts\python.exe main.py --crawler fred
```

5. Verify macro data in Postgres:

```bash
docker exec -it postgres psql -U admin -d market_db -c "
SELECT series_id, observation_date, value, unit
FROM macro_observations
WHERE observation_date >= CURRENT_DATE - 7
ORDER BY series_id, observation_date DESC;"
```

### Setup (yfinance market proxies)

No API key required. Uses `config/market_tickers.yaml` (VIX, DXY, GOLD, WTI, SPY, QQQ, TLT, HYG).

Ingest market prices into `macro_*` tables (`source = yfinance`):

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe main.py --crawler market --persist
```

Preview without DB write:

```powershell
.\.venv\Scripts\python.exe main.py --crawler market
```

Verify yfinance rows in Postgres:

```bash
docker exec -it postgres psql -U admin -d market_db -c "
SELECT series_id, observation_date, value, unit
FROM macro_observations
WHERE source = 'yfinance'
ORDER BY observation_date DESC, series_id;"
```

Persist FRED + Kalshi + market in one command:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe main.py --persist-all
```

Compute signals from persisted data (read-only):

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe main.py --signals
```

Preview all crawlers (fred/market live APIs; nyfed/polymarket are stubs):

```powershell
.\.venv\Scripts\python.exe main.py --crawler all
```

## Success criteria

**MVP:** a user can ask a macro/liquidity/risk question and get a useful answer grounded in DB rows and signals, with verifiable citations.

**v1:** weekly retention, brief/alerts optional, 3–5 pilot users willing to pay.

## Roadmap (high level)

- **Phase 1**: Reliable ingestion + Postgres (in progress)
- **Phase 2**: Grounded Q&A (structured retrieval + LLM) + signal context
- **Phase 3**: UI + briefs/alerts as KB artifacts
- **v1+**: pgvector / embeddings for unstructured notes (not MVP)
- **Phase 4**: Insiders/flows, pilots, paid validation

## Repository rename (local + GitHub)

Code uses package `macromind` under `src/macromind`. To match the product name on disk and GitHub:

1. **Close Cursor** (or any process using this folder).
2. **Rename folder:** `D:\projects\AI-Market-Terminal` → `D:\projects\MacroMind`
3. **Re-open** the project from `D:\projects\MacroMind`
4. **GitHub:** Settings → General → Repository name → `MacroMind`, then update your remote:
   ```powershell
   git remote set-url origin https://github.com/Dimon2/MacroMind.git
   ```

## Project docs

- Product specification: `product.md`
- Data source map: `macromind_data_sources_en.pdf`
