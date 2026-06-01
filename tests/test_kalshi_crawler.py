from __future__ import annotations

from datetime import date, datetime, timezone

from ai_market_terminal.crawlers.kalshi_crawler import KalshiCrawler
from ai_market_terminal.prediction_markets.models import PredictionMarketSnapshot


def test_snapshot_to_datapoint_maps_core_fields() -> None:
    fetched = datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc)
    snapshot = PredictionMarketSnapshot(
        platform="kalshi",
        series_ticker="KXFED",
        macro_topic="fed",
        event_ticker="KXFED-26MAY",
        market_ticker="KXFED-26MAY-T4.25",
        outcome_type="threshold",
        outcome_label="4.25%",
        yes_probability=0.42,
        period_date=date(2026, 5, 31),
        fetched_at=fetched,
        url="https://kalshi.com/markets/kxfed/example",
    )

    dp = KalshiCrawler._snapshot_to_datapoint(snapshot)

    assert dp.source == "kalshi"
    assert dp.indicator == "KXFED-26MAY-T4.25"
    assert dp.value == 0.42
    assert dp.unit == "probability"
    assert dp.period == "2026-05-31"
    assert dp.fetched_at == fetched
    assert dp.metadata["series_ticker"] == "KXFED"
    assert dp.metadata["event_ticker"] == "KXFED-26MAY"
    assert dp.metadata["outcome_label"] == "4.25%"
    assert dp.metadata["url"] == snapshot.url
    assert "yes_probability" not in dp.metadata
