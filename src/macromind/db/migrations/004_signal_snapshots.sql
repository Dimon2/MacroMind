-- Daily signal snapshots (history + day-over-day deltas)

CREATE TABLE IF NOT EXISTS signal_snapshots (
  id              BIGSERIAL PRIMARY KEY,
  snapshot_date   DATE NOT NULL,
  signal_name     TEXT NOT NULL,
  status          TEXT NOT NULL CHECK (status IN ('computed', 'skipped')),
  value           NUMERIC,
  label           TEXT,
  reason          TEXT,
  inputs          JSONB NOT NULL DEFAULT '{}',
  metadata        JSONB NOT NULL DEFAULT '{}',
  as_of           TIMESTAMPTZ NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (snapshot_date, signal_name)
);

CREATE INDEX IF NOT EXISTS idx_signal_snapshots_date
  ON signal_snapshots (snapshot_date DESC);
