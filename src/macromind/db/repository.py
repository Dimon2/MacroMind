from __future__ import annotations

from datetime import date, datetime, timezone

from macromind.db.connection import connection_scope
from macromind.db.crawl_run import CrawlRunRecord, truncate_error_text
from macromind.models import DataPoint
from macromind.prediction_markets.models import PredictionMarketSnapshot


class PredictionMarketRepository:
    def save_snapshots(self, snapshots: list[PredictionMarketSnapshot]) -> int:
        if not snapshots:
            return 0

        saved = 0
        with connection_scope() as conn:
            for snap in snapshots:
                self._upsert_series(conn, snap)
                self._upsert_event(conn, snap)
                self._upsert_market(conn, snap)
                self._upsert_observation(conn, snap)
                saved += 1
        return saved

    def load_latest_snapshots(self) -> list[PredictionMarketSnapshot]:
        with connection_scope() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT ON (obs.platform, obs.market_ticker)
                  obs.platform,
                  series.series_ticker,
                  series.macro_topic,
                  events.event_ticker,
                  obs.market_ticker,
                  markets.outcome_type,
                  markets.outcome_label,
                  obs.yes_probability,
                  obs.period_date,
                  obs.fetched_at,
                  markets.outcome_key,
                  markets.strike,
                  markets.strike_op,
                  markets.unit_hint,
                  series.slug,
                  series.title,
                  events.title,
                  events.reference_period,
                  events.event_close_at,
                  obs.yes_bid,
                  obs.yes_ask,
                  obs.volume,
                  markets.url
                FROM pm_observations AS obs
                JOIN pm_markets AS markets
                  ON markets.platform = obs.platform
                 AND markets.market_ticker = obs.market_ticker
                JOIN pm_events AS events
                  ON events.platform = markets.platform
                 AND events.event_ticker = markets.event_ticker
                JOIN pm_series AS series
                  ON series.platform = events.platform
                 AND series.series_ticker = events.series_ticker
                ORDER BY obs.platform, obs.market_ticker, obs.period_date DESC, obs.fetched_at DESC
                """
            ).fetchall()
        return [self._row_to_snapshot(row) for row in rows]

    def _upsert_series(self, conn, snap: PredictionMarketSnapshot) -> None:
        conn.execute(
            """
            INSERT INTO pm_series (platform, series_ticker, macro_topic, slug, title, is_watched)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (platform, series_ticker) DO UPDATE SET
              macro_topic = EXCLUDED.macro_topic,
              slug = COALESCE(EXCLUDED.slug, pm_series.slug),
              title = COALESCE(EXCLUDED.title, pm_series.title)
            """,
            (
                snap.platform,
                snap.series_ticker,
                snap.macro_topic,
                snap.series_slug,
                snap.series_title,
            ),
        )

    def _upsert_event(self, conn, snap: PredictionMarketSnapshot) -> None:
        event_url = None
        if snap.url:
            parts = snap.url.rsplit("/", 1)
            event_url = parts[0] if len(parts) > 1 else snap.url

        conn.execute(
            """
            INSERT INTO pm_events (
              platform, event_ticker, series_ticker, title,
              reference_period, event_close_at, url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (platform, event_ticker) DO UPDATE SET
              title = COALESCE(EXCLUDED.title, pm_events.title),
              reference_period = COALESCE(EXCLUDED.reference_period, pm_events.reference_period),
              event_close_at = COALESCE(EXCLUDED.event_close_at, pm_events.event_close_at),
              url = COALESCE(EXCLUDED.url, pm_events.url)
            """,
            (
                snap.platform,
                snap.event_ticker,
                snap.series_ticker,
                snap.event_title,
                snap.reference_period,
                snap.event_close_at,
                event_url,
            ),
        )

    def _upsert_market(self, conn, snap: PredictionMarketSnapshot) -> None:
        conn.execute(
            """
            INSERT INTO pm_markets (
              platform, market_ticker, event_ticker, outcome_type,
              outcome_label, outcome_key, strike, strike_op, unit_hint, url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (platform, market_ticker) DO UPDATE SET
              outcome_label = EXCLUDED.outcome_label,
              outcome_key = EXCLUDED.outcome_key,
              strike = EXCLUDED.strike,
              strike_op = EXCLUDED.strike_op,
              unit_hint = EXCLUDED.unit_hint,
              url = EXCLUDED.url
            """,
            (
                snap.platform,
                snap.market_ticker,
                snap.event_ticker,
                snap.outcome_type,
                snap.outcome_label,
                snap.outcome_key,
                snap.strike,
                snap.strike_op,
                snap.unit_hint,
                snap.url,
            ),
        )

    def _upsert_observation(self, conn, snap: PredictionMarketSnapshot) -> None:
        conn.execute(
            """
            INSERT INTO pm_observations (
              platform, market_ticker, period_date, yes_probability,
              yes_bid, yes_ask, volume, fetched_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (platform, market_ticker, period_date) DO UPDATE SET
              yes_probability = EXCLUDED.yes_probability,
              yes_bid = EXCLUDED.yes_bid,
              yes_ask = EXCLUDED.yes_ask,
              volume = EXCLUDED.volume,
              fetched_at = EXCLUDED.fetched_at
            """,
            (
                snap.platform,
                snap.market_ticker,
                snap.period_date,
                snap.yes_probability,
                snap.yes_bid,
                snap.yes_ask,
                snap.volume,
                snap.fetched_at,
            ),
        )

    @staticmethod
    def _row_to_snapshot(row: tuple) -> PredictionMarketSnapshot:
        return PredictionMarketSnapshot(
            platform=row[0],
            series_ticker=row[1],
            macro_topic=row[2],
            event_ticker=row[3],
            market_ticker=row[4],
            outcome_type=row[5],
            outcome_label=row[6],
            yes_probability=float(row[7]),
            period_date=row[8],
            fetched_at=row[9],
            outcome_key=row[10],
            strike=float(row[11]) if row[11] is not None else None,
            strike_op=row[12],
            unit_hint=row[13],
            series_slug=row[14],
            series_title=row[15],
            event_title=row[16],
            reference_period=row[17],
            event_close_at=row[18],
            yes_bid=float(row[19]) if row[19] is not None else None,
            yes_ask=float(row[20]) if row[20] is not None else None,
            volume=float(row[21]) if row[21] is not None else None,
            url=row[22],
        )


class MacroRepository:
    def save_datapoints(self, datapoints: list[DataPoint]) -> int:
        if not datapoints:
            return 0

        saved = 0
        with connection_scope() as conn:
            for dp in datapoints:
                self._upsert_series(conn, dp)
                self._upsert_observation(conn, dp)
                saved += 1
        return saved

    def load_latest_datapoints(self) -> list[DataPoint]:
        with connection_scope() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT ON (obs.source, obs.series_id)
                  obs.source,
                  obs.series_id,
                  obs.value,
                  obs.unit,
                  obs.observation_date,
                  obs.fetched_at,
                  series.title,
                  series.frequency,
                  series.category
                FROM macro_observations AS obs
                JOIN macro_series AS series
                  ON series.source = obs.source
                 AND series.series_id = obs.series_id
                ORDER BY obs.source, obs.series_id, obs.observation_date DESC, obs.fetched_at DESC
                """
            ).fetchall()
        return [self._row_to_datapoint(row) for row in rows]

    def _upsert_series(self, conn, dp: DataPoint) -> None:
        metadata = dp.metadata or {}
        conn.execute(
            """
            INSERT INTO macro_series (
              source, series_id, title, units, frequency, category, is_watched
            )
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (source, series_id) DO UPDATE SET
              title = COALESCE(EXCLUDED.title, macro_series.title),
              units = COALESCE(EXCLUDED.units, macro_series.units),
              frequency = COALESCE(EXCLUDED.frequency, macro_series.frequency),
              category = COALESCE(EXCLUDED.category, macro_series.category)
            """,
            (
                dp.source,
                dp.indicator,
                metadata.get("title"),
                dp.unit,
                metadata.get("frequency") or metadata.get("frequency_short"),
                metadata.get("category"),
            ),
        )

    def _upsert_observation(self, conn, dp: DataPoint) -> None:
        observation_date = date.fromisoformat(dp.period)
        conn.execute(
            """
            INSERT INTO macro_observations (
              source, series_id, observation_date, value, unit, fetched_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, series_id, observation_date) DO UPDATE SET
              value = EXCLUDED.value,
              unit = EXCLUDED.unit,
              fetched_at = EXCLUDED.fetched_at
            """,
            (
                dp.source,
                dp.indicator,
                observation_date,
                dp.value,
                dp.unit,
                dp.fetched_at,
            ),
        )

    @staticmethod
    def _row_to_datapoint(row: tuple) -> DataPoint:
        metadata: dict[str, str] = {}
        if row[6] is not None:
            metadata["title"] = row[6]
        if row[7] is not None:
            metadata["frequency"] = row[7]
        if row[8] is not None:
            metadata["category"] = row[8]
        return DataPoint(
            source=row[0],
            indicator=row[1],
            value=float(row[2]),
            unit=row[3] or "",
            period=row[4].isoformat(),
            fetched_at=_as_utc_datetime(row[5]),
            metadata=metadata,
        )


class CrawlRunRepository:
    def record_run(self, record: CrawlRunRecord) -> None:
        with connection_scope() as conn:
            conn.execute(
                """
                INSERT INTO crawl_runs (
                  crawler, started_at, finished_at, status, rows_persisted, error_text
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    record.crawler,
                    record.started_at,
                    record.finished_at,
                    record.status,
                    record.rows_persisted,
                    truncate_error_text(record.error_text),
                ),
            )

    def load_last_success_by_crawler(self) -> dict[str, CrawlRunRecord]:
        return self._load_latest_by_crawler(status="success")

    def load_last_run_by_crawler(self) -> dict[str, CrawlRunRecord]:
        return self._load_latest_by_crawler(status=None)

    def _load_latest_by_crawler(
        self, *, status: str | None
    ) -> dict[str, CrawlRunRecord]:
        where_clause = "WHERE status = %s" if status is not None else ""
        params: tuple[object, ...] = (status,) if status is not None else ()

        with connection_scope() as conn:
            rows = conn.execute(
                f"""
                SELECT DISTINCT ON (crawler)
                  crawler, started_at, finished_at, status, rows_persisted, error_text
                FROM crawl_runs
                {where_clause}
                ORDER BY crawler, finished_at DESC
                """,
                params,
            ).fetchall()

        return {row[0]: self._row_to_record(row) for row in rows}

    @staticmethod
    def _row_to_record(row: tuple) -> CrawlRunRecord:
        return CrawlRunRecord(
            crawler=row[0],
            started_at=_as_utc_datetime(row[1]),
            finished_at=_as_utc_datetime(row[2]),
            status=row[3],
            rows_persisted=int(row[4]),
            error_text=row[5],
        )


def _as_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
