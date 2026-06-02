from __future__ import annotations

from datetime import date, datetime, timezone

from ai_market_terminal.market.normalized_observation import NormalizedObservation
from ai_market_terminal.signals.service import SignalService


def test_signal_service_returns_coverage_and_signals() -> None:
    service = SignalService()
    observations = [
        NormalizedObservation(
            source="yfinance",
            series_key="SPY",
            observation_date=date(2026, 6, 1),
            fetched_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
            value_kind="level",
            value=500.0,
            unit="usd",
            metadata={"change_pct": 1.2},
        ),
        NormalizedObservation(
            source="yfinance",
            series_key="VIX",
            observation_date=date(2026, 6, 1),
            fetched_at=datetime(2026, 6, 2, 10, 1, tzinfo=timezone.utc),
            value_kind="level",
            value=17.5,
            unit="index",
            metadata={},
        ),
        NormalizedObservation(
            source="kalshi",
            series_key="KXCPI-1",
            observation_date=date(2026, 6, 1),
            fetched_at=datetime(2026, 6, 2, 10, 2, tzinfo=timezone.utc),
            value_kind="probability",
            value=0.55,
            unit="probability",
            metadata={"macro_topic": "inflation"},
        ),
    ]
    result = service.compute(observations)
    assert result["coverage"]["total"] == 3
    assert result["coverage"]["computed"] >= 2
    assert len(result["signals"]) == 3


def test_signal_service_handles_degraded_inputs() -> None:
    service = SignalService()
    result = service.compute([])
    assert result["coverage"] == {"computed": 0, "skipped": 3, "total": 3}
