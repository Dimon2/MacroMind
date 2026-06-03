-- Crawler persist run log (freshness / operational visibility)

CREATE TABLE IF NOT EXISTS crawl_runs (
  id              BIGSERIAL PRIMARY KEY,
  crawler         TEXT NOT NULL,
  started_at      TIMESTAMPTZ NOT NULL,
  finished_at     TIMESTAMPTZ NOT NULL,
  status          TEXT NOT NULL CHECK (status IN ('success', 'failure')),
  rows_persisted  INTEGER NOT NULL DEFAULT 0,
  error_text      TEXT
);

CREATE INDEX IF NOT EXISTS idx_crawl_runs_crawler_finished
  ON crawl_runs (crawler, finished_at DESC);
