-- Prediction markets schema (Kalshi, Polymarket, etc.)

CREATE TABLE IF NOT EXISTS pm_series (
  platform       TEXT NOT NULL DEFAULT 'kalshi',
  series_ticker  TEXT NOT NULL,
  macro_topic    TEXT NOT NULL,
  slug           TEXT,
  title          TEXT,
  is_watched     BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (platform, series_ticker)
);

CREATE TABLE IF NOT EXISTS pm_events (
  platform          TEXT NOT NULL DEFAULT 'kalshi',
  event_ticker      TEXT NOT NULL,
  series_ticker     TEXT NOT NULL,
  title             TEXT,
  reference_period  TEXT,
  event_close_at    TIMESTAMPTZ,
  url               TEXT,
  discovered_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (platform, event_ticker),
  FOREIGN KEY (platform, series_ticker) REFERENCES pm_series (platform, series_ticker)
);

CREATE TABLE IF NOT EXISTS pm_markets (
  platform        TEXT NOT NULL DEFAULT 'kalshi',
  market_ticker   TEXT NOT NULL,
  event_ticker    TEXT NOT NULL,
  outcome_type    TEXT NOT NULL,
  outcome_label   TEXT NOT NULL,
  outcome_key     TEXT,
  strike          NUMERIC,
  strike_op       TEXT,
  unit_hint       TEXT,
  url             TEXT,
  PRIMARY KEY (platform, market_ticker),
  FOREIGN KEY (platform, event_ticker) REFERENCES pm_events (platform, event_ticker)
);

CREATE TABLE IF NOT EXISTS pm_observations (
  id              BIGSERIAL PRIMARY KEY,
  platform        TEXT NOT NULL DEFAULT 'kalshi',
  market_ticker   TEXT NOT NULL,
  period_date     DATE NOT NULL,
  yes_probability NUMERIC(7, 6) NOT NULL,
  yes_bid         NUMERIC(7, 6),
  yes_ask         NUMERIC(7, 6),
  volume          NUMERIC,
  fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (platform, market_ticker, period_date),
  FOREIGN KEY (platform, market_ticker) REFERENCES pm_markets (platform, market_ticker)
);

CREATE INDEX IF NOT EXISTS idx_pm_obs_period_date ON pm_observations (period_date);
CREATE INDEX IF NOT EXISTS idx_pm_events_series ON pm_events (platform, series_ticker);
