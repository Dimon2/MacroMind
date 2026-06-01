-- Macro economic timeseries (FRED, etc.)

CREATE TABLE IF NOT EXISTS macro_series (
  source      TEXT NOT NULL DEFAULT 'fred',
  series_id   TEXT NOT NULL,
  title       TEXT,
  units       TEXT,
  frequency   TEXT,
  category    TEXT,
  is_watched  BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (source, series_id)
);

CREATE TABLE IF NOT EXISTS macro_observations (
  id               BIGSERIAL PRIMARY KEY,
  source           TEXT NOT NULL DEFAULT 'fred',
  series_id        TEXT NOT NULL,
  observation_date DATE NOT NULL,
  value            NUMERIC NOT NULL,
  unit             TEXT,
  fetched_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source, series_id, observation_date),
  FOREIGN KEY (source, series_id) REFERENCES macro_series (source, series_id)
);

CREATE INDEX IF NOT EXISTS idx_macro_obs_date ON macro_observations (observation_date);
CREATE INDEX IF NOT EXISTS idx_macro_obs_series ON macro_observations (source, series_id);
