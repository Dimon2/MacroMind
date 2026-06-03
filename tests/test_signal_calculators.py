from __future__ import annotations

from datetime import date, datetime, timezone

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.calculators import (
    compute_growth_regime,
    compute_inflation_regime,
    compute_liquidity_regime,
    compute_macro_implied_inflation_prob,
    compute_market_state,
    compute_rates_curve_proxy,
    compute_risk_regime,
)
from macromind.signals.models import SignalResult

_FETCHED = datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc)


def _fred_obs(
    series_key: str,
    observation_date: date,
    value: float,
    *,
    value_kind: str = "level",
) -> NormalizedObservation:
    return NormalizedObservation(
        source="fred",
        series_key=series_key,
        observation_date=observation_date,
        fetched_at=_FETCHED,
        value_kind=value_kind,
        value=value,
        unit="index",
        metadata={"category": "macro"},
    )


def _cpi_history_desc(values_newest_first: list[float]) -> list[NormalizedObservation]:
    observations: list[NormalizedObservation] = []
    year, month = 2026, 4
    for value in values_newest_first:
        observations.append(_fred_obs("CPIAUCSL", date(year, month, 1), value))
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    return observations


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


def test_compute_liquidity_regime_easy_on_walcl_growth() -> None:
    observations = [
        _fred_obs("WALCL", date(2026, 6, 4), 8_000_000.0),
        _fred_obs("WALCL", date(2026, 5, 28), 7_900_000.0),
    ]
    result = compute_liquidity_regime(observations)
    assert result.status == "computed"
    assert result.metadata["label"] == "easy"


def test_compute_liquidity_regime_skips_without_history() -> None:
    result = compute_liquidity_regime([_fred_obs("WALCL", date(2026, 6, 4), 1.0)])
    assert result.status == "skipped"
    assert result.reason == "insufficient_history"


def test_compute_inflation_regime_stable_yoy() -> None:
    values = [310.0] + [308.0] * 11 + [300.0]
    result = compute_inflation_regime(_cpi_history_desc(values))
    assert result.status == "computed"
    assert result.metadata["label"] == "stable"
    assert abs(result.value - ((310.0 / 300.0 - 1) * 100)) < 0.01


def test_compute_inflation_regime_rising_yoy() -> None:
    values = [330.0] + [310.0] * 11 + [300.0]
    result = compute_inflation_regime(_cpi_history_desc(values))
    assert result.status == "computed"
    assert result.metadata["label"] == "rising"


def test_compute_inflation_regime_skips_short_history() -> None:
    result = compute_inflation_regime(
        [_fred_obs("CPIAUCSL", date(2026, 4, 1), 310.0), _fred_obs("CPIAUCSL", date(2026, 3, 1), 308.0)]
    )
    assert result.status == "skipped"
    assert result.reason == "insufficient_history"


def test_compute_growth_regime_expanding() -> None:
    observations = [
        _fred_obs("UNRATE", date(2026, 5, 1), 3.8, value_kind="rate"),
        _fred_obs("UNRATE", date(2026, 4, 1), 4.1, value_kind="rate"),
        _fred_obs("T10Y2Y", date(2026, 6, 1), 0.5, value_kind="spread"),
        NormalizedObservation(
            source="yfinance",
            series_key="SPY",
            observation_date=date(2026, 6, 1),
            fetched_at=_FETCHED,
            value_kind="level",
            value=500.0,
            unit="usd",
            metadata={"change_pct": 0.5},
        ),
    ]
    result = compute_growth_regime(observations)
    assert result.status == "computed"
    assert result.metadata["label"] == "expanding"


def test_compute_growth_regime_skips_without_unrate_history() -> None:
    result = compute_growth_regime([_fred_obs("UNRATE", date(2026, 5, 1), 4.0, value_kind="rate")])
    assert result.status == "skipped"
    assert result.reason == "insufficient_history"


def _dimension_result(name: str, label: str) -> SignalResult:
    return SignalResult(
        name=name,
        status="computed",
        value=1.0,
        metadata={"label": label},
        as_of=_FETCHED,
    )


def test_compute_market_state_composite_label() -> None:
    result = compute_market_state(
        {
            "risk_regime": _dimension_result("risk_regime", "risk_on"),
            "liquidity_regime": _dimension_result("liquidity_regime", "tight"),
            "inflation_regime": _dimension_result("inflation_regime", "rising"),
            "growth_regime": _dimension_result("growth_regime", "expanding"),
        }
    )
    assert result.status == "computed"
    assert result.metadata["label"] == "risk_on_tight_rising_expanding"
    assert result.inputs["dimensions"]["liquidity_regime"] == "tight"


def test_compute_market_state_skips_when_dimension_missing() -> None:
    result = compute_market_state(
        {
            "risk_regime": _dimension_result("risk_regime", "risk_on"),
            "liquidity_regime": SignalResult(
                name="liquidity_regime",
                status="skipped",
                reason="insufficient_history",
            ),
            "inflation_regime": _dimension_result("inflation_regime", "stable"),
            "growth_regime": _dimension_result("growth_regime", "neutral"),
        }
    )
    assert result.status == "skipped"
    assert result.reason == "missing_dimension_labels"
    assert "liquidity_regime" in result.inputs["missing"]
