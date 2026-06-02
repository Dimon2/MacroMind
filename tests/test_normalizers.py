from __future__ import annotations

from datetime import date, datetime, timezone

from macromind.market.normalized_feed_service import NormalizedFeedService
from macromind.market.normalizers import (
    normalize_macro_datapoint,
    normalize_prediction_snapshot,
)
from macromind.models import DataPoint
from macromind.prediction_markets.models import PredictionMarketSnapshot


def test_normalize_macro_datapoint_level() -> None:
    datapoint = DataPoint(
        source="yfinance",
        indicator="VIX",
        value=17.25,
        unit="index",
        period="2026-06-01",
        fetched_at=datetime(2026, 6, 2, 8, 30, tzinfo=timezone.utc),
        metadata={"category": "sentiment"},
    )

    result = normalize_macro_datapoint(datapoint)

    assert result.source == "yfinance"
    assert result.series_key == "VIX"
    assert result.observation_date == date(2026, 6, 1)
    assert result.value_kind == "level"
    assert result.unit == "index"
    assert result.metadata["indicator"] == "VIX"
    assert result.metadata["category"] == "sentiment"


def test_normalize_macro_datapoint_rate() -> None:
    datapoint = DataPoint(
        source="fred",
        indicator="UNRATE",
        value=4.1,
        unit="percent",
        period="2026-05-01",
        fetched_at=datetime(2026, 6, 2, 8, 31, tzinfo=timezone.utc),
    )

    result = normalize_macro_datapoint(datapoint)

    assert result.value_kind == "rate"


def test_normalize_prediction_snapshot_probability() -> None:
    snapshot = PredictionMarketSnapshot(
        platform="kalshi",
        series_ticker="KXCPIYOY",
        macro_topic="inflation",
        event_ticker="KXCPIYOY-26MAY",
        market_ticker="KXCPIYOY-26MAY-T3.0",
        outcome_type="threshold",
        outcome_label="Above 3.0%",
        yes_probability=0.41,
        period_date=date(2026, 5, 1),
        fetched_at=datetime(2026, 6, 2, 8, 32, tzinfo=timezone.utc),
        strike=3.0,
        strike_op="gt",
        yes_bid=0.40,
        yes_ask=0.42,
        volume=12000.0,
        event_close_at=datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc),
    )

    result = normalize_prediction_snapshot(snapshot)

    assert result.source == "kalshi"
    assert result.series_key == "KXCPIYOY-26MAY-T3.0"
    assert result.observation_date == date(2026, 5, 1)
    assert result.value_kind == "probability"
    assert result.value == 0.41
    assert result.metadata["yes_bid"] == 0.40
    assert result.metadata["yes_ask"] == 0.42
    assert result.metadata["event_close_at"] == "2026-06-15T12:00:00+00:00"


def test_normalized_feed_service_combines_sources() -> None:
    service = NormalizedFeedService()
    macro = [
        DataPoint(
            source="fred",
            indicator="CPIAUCSL",
            value=300.0,
            unit="index",
            period="2026-05-01",
            fetched_at=datetime(2026, 6, 2, 8, 33, tzinfo=timezone.utc),
        )
    ]
    pm = [
        PredictionMarketSnapshot(
            platform="kalshi",
            series_ticker="KXU3",
            macro_topic="employment",
            event_ticker="KXU3-26MAY",
            market_ticker="KXU3-26MAY-T4.2",
            outcome_type="threshold",
            outcome_label="Above 4.2%",
            yes_probability=0.35,
            period_date=date(2026, 5, 1),
            fetched_at=datetime(2026, 6, 2, 8, 34, tzinfo=timezone.utc),
        )
    ]

    result = service.combine(macro_datapoints=macro, prediction_snapshots=pm)

    assert len(result) == 2
    assert {item.source for item in result} == {"fred", "kalshi"}
    assert all(item.observation_date == date(2026, 5, 1) for item in result)
