from __future__ import annotations

from datetime import date, datetime, timezone

from ai_market_terminal.market.normalized_observation import NormalizedObservation
from ai_market_terminal.signals.calculators import (
    compute_macro_implied_inflation_prob,
    compute_rates_curve_proxy,
    compute_risk_regime,
)


def test_compute_risk_regime_computed() -> None:
    observations = [
        NormalizedObservation(
            source="yfinance",
            series_key="SPY",
            observation_date=date(2026, 6, 1),
            fetched_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
            value_kind="level",
            value=505.0,
            unit="usd",
            metadata={"change_pct": 0.9},
        ),
        NormalizedObservation(
            source="yfinance",
            series_key="VIX",
            observation_date=date(2026, 6, 1),
            fetched_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
            value_kind="level",
            value=18.0,
            unit="index",
            metadata={},
        ),
    ]
    result = compute_risk_regime(observations)
    assert result.status == "computed"
    assert result.value == 2.0
    assert result.metadata["label"] == "risk_on"


def test_compute_rates_curve_proxy_uses_t10y2y() -> None:
    observations = [
        NormalizedObservation(
            source="fred",
            series_key="T10Y2Y",
            observation_date=date(2026, 6, 1),
            fetched_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
            value_kind="spread",
            value=-0.2,
            unit="pct",
            metadata={},
        )
    ]
    result = compute_rates_curve_proxy(observations)
    assert result.status == "computed"
    assert result.value == -0.2
    assert result.metadata["curve_state"] == "inverted"


def test_compute_macro_implied_inflation_prob_average() -> None:
    observations = [
        NormalizedObservation(
            source="kalshi",
            series_key="KXCPI-1",
            observation_date=date(2026, 6, 1),
            fetched_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
            value_kind="probability",
            value=0.4,
            unit="probability",
            metadata={"macro_topic": "inflation"},
        ),
        NormalizedObservation(
            source="kalshi",
            series_key="KXCPI-2",
            observation_date=date(2026, 6, 1),
            fetched_at=datetime(2026, 6, 2, 10, 1, tzinfo=timezone.utc),
            value_kind="probability",
            value=0.6,
            unit="probability",
            metadata={"macro_topic": "inflation"},
        ),
    ]
    result = compute_macro_implied_inflation_prob(observations)
    assert result.status == "computed"
    assert result.value == 0.5
    assert result.inputs["markets_count"] == 2


def test_compute_risk_regime_skips_when_missing_inputs() -> None:
    result = compute_risk_regime([])
    assert result.status == "skipped"
    assert result.reason == "missing_required_inputs"
