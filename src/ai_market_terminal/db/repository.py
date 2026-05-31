from __future__ import annotations

from ai_market_terminal.db.connection import connection_scope
from ai_market_terminal.prediction_markets.models import PredictionMarketSnapshot


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
