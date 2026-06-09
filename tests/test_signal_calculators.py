from __future__ import annotations

from datetime import date, datetime, timezone

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.calculators import (
    INFLATION_YOY_RISING_PCT,
    compute_credit_regime,
    compute_growth_regime,
    compute_inflation_regime,
    compute_liquidity_regime,
    compute_market_state,
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


def _m2_history_desc(values_newest_first: list[float]) -> list[NormalizedObservation]:
    observations: list[NormalizedObservation] = []
    year, month = 2026, 4
    for value in values_newest_first:
        observations.append(_fred_obs("M2SL", date(year, month, 1), value))
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    return observations


def _net_liquidity_obs(
    obs_date: date,
    *,
    walcl: float,
    tga: float,
    rrp_billions: float,
) -> list[NormalizedObservation]:
    return [
        _fred_obs("WALCL", obs_date, walcl),
        _fred_obs("WTREGEN", obs_date, tga),
        _fred_obs("RRPONTSYD", obs_date, rrp_billions),
    ]


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


def test_compute_risk_regime_skips_when_missing_inputs() -> None:
    result = compute_risk_regime([])
    assert result.status == "skipped"
    assert result.reason == "missing_required_inputs"


def test_compute_liquidity_regime_net_liquidity_easy() -> None:
    observations = [
        *_net_liquidity_obs(date(2026, 6, 4), walcl=8_100_000.0, tga=500_000.0, rrp_billions=500.0),
        *_net_liquidity_obs(date(2026, 5, 28), walcl=8_000_000.0, tga=500_000.0, rrp_billions=500.0),
    ]
    result = compute_liquidity_regime(observations)
    assert result.status == "computed"
    assert result.metadata["label"] == "easy"
    assert result.inputs["net_liquidity"] == 8_100_000.0 - 500_000.0 - 500_000.0


def test_compute_liquidity_regime_rrp_unit_conversion() -> None:
    observations = [
        *_net_liquidity_obs(date(2026, 6, 4), walcl=1_000_000.0, tga=0.0, rrp_billions=1.0),
    ]
    result = compute_liquidity_regime(observations)
    assert result.status == "skipped"
    assert result.inputs["aligned_points"] == 1


def test_compute_liquidity_regime_m2_mom_and_yoy() -> None:
    m2_values = [23000.0] + [22800.0] * 11 + [22000.0]
    observations = [
        *_net_liquidity_obs(date(2026, 6, 4), walcl=8_000_000.0, tga=500_000.0, rrp_billions=500.0),
        *_net_liquidity_obs(date(2026, 5, 28), walcl=7_950_000.0, tga=500_000.0, rrp_billions=500.0),
        *_m2_history_desc(m2_values),
    ]
    result = compute_liquidity_regime(observations)
    assert result.status == "computed"
    assert result.inputs["M2SL_change_mom_pct"] is not None
    assert result.inputs["M2SL_yoy_status"] == "computed"
    assert result.inputs["M2SL_yoy_pct"] is not None


def test_compute_liquidity_regime_m2_yoy_insufficient_history() -> None:
    observations = [
        *_net_liquidity_obs(date(2026, 6, 4), walcl=8_000_000.0, tga=500_000.0, rrp_billions=500.0),
        *_net_liquidity_obs(date(2026, 5, 28), walcl=7_950_000.0, tga=500_000.0, rrp_billions=500.0),
        _fred_obs("M2SL", date(2026, 4, 1), 22800.0),
        _fred_obs("M2SL", date(2026, 3, 1), 22700.0),
    ]
    result = compute_liquidity_regime(observations)
    assert result.status == "computed"
    assert result.inputs["M2SL_yoy_status"] == "insufficient_history"


def test_compute_credit_regime_relaxed() -> None:
    observations = [
        NormalizedObservation(
            source="fred",
            series_key="BAMLH0A0HYM2",
            observation_date=date(2026, 6, 1),
            fetched_at=_FETCHED,
            value_kind="rate",
            value=3.0,
            unit="percent",
            metadata={},
        )
    ]
    result = compute_credit_regime(observations)
    assert result.status == "computed"
    assert result.metadata["label"] == "relaxed"


def test_compute_credit_regime_stressed_with_hyg() -> None:
    observations = [
        NormalizedObservation(
            source="fred",
            series_key="BAMLH0A0HYM2",
            observation_date=date(2026, 6, 1),
            fetched_at=_FETCHED,
            value_kind="rate",
            value=6.0,
            unit="percent",
            metadata={},
        ),
        NormalizedObservation(
            source="yfinance",
            series_key="HYG",
            observation_date=date(2026, 6, 1),
            fetched_at=_FETCHED,
            value_kind="level",
            value=75.0,
            unit="usd",
            metadata={"change_pct": -1.2},
        ),
    ]
    result = compute_credit_regime(observations)
    assert result.metadata["label"] == "stressed"
    assert result.inputs["HYG_change_pct"] == -1.2


def test_compute_inflation_regime_stable_yoy() -> None:
    values = [310.0] + [308.0] * 11 + [300.0]
    result = compute_inflation_regime(_cpi_history_desc(values))
    assert result.status == "computed"
    assert result.metadata["label"] == "stable"
    assert abs(result.value - ((310.0 / 300.0 - 1) * 100)) < 0.01
    assert result.inputs["headline_yoy_pct"] == result.value


def test_compute_inflation_regime_label_uses_headline_only() -> None:
    headline = _cpi_history_desc([310.0] + [308.0] * 11 + [300.0])
    core_values = [320.0] + [318.0] * 11 + [290.0]
    core: list[NormalizedObservation] = []
    year, month = 2026, 4
    for value in core_values:
        core.append(_fred_obs("CPILFESL", date(year, month, 1), value))
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    result = compute_inflation_regime([*headline, *core])
    assert result.metadata["label"] == "stable"
    assert result.inputs["core_yoy_pct"] is not None
    assert result.inputs["core_yoy_pct"] > INFLATION_YOY_RISING_PCT


def test_compute_growth_regime_spy_does_not_affect_score() -> None:
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
            metadata={"change_pct": -2.0},
        ),
    ]
    result = compute_growth_regime(observations)
    assert result.metadata["label"] == "expanding"
    assert result.value == 3.0
    assert result.inputs["SPY_change_pct"] == -2.0


def test_compute_growth_regime_includes_curve_in_inputs() -> None:
    observations = [
        _fred_obs("UNRATE", date(2026, 5, 1), 3.8, value_kind="rate"),
        _fred_obs("UNRATE", date(2026, 4, 1), 4.1, value_kind="rate"),
        _fred_obs("T10Y2Y", date(2026, 6, 1), 0.5, value_kind="spread"),
    ]
    result = compute_growth_regime(observations)
    assert result.status == "computed"
    assert result.inputs["curve_spread"] == 0.5
    assert result.inputs["curve_state"] == "normal"
    assert result.inputs["curve_source"] == "T10Y2Y"


def _dimension_result(name: str, label: str) -> SignalResult:
    return SignalResult(
        name=name,
        status="computed",
        value=1.0,
        metadata={"label": label},
        as_of=_FETCHED,
    )


def test_compute_market_state_five_part_composite() -> None:
    result = compute_market_state(
        {
            "risk_regime": _dimension_result("risk_regime", "risk_on"),
            "liquidity_regime": _dimension_result("liquidity_regime", "tight"),
            "inflation_regime": _dimension_result("inflation_regime", "rising"),
            "growth_regime": _dimension_result("growth_regime", "expanding"),
            "credit_regime": _dimension_result("credit_regime", "normal"),
        }
    )
    assert result.status == "computed"
    assert result.metadata["label"] == "risk_on_tight_rising_expanding_normal"


def test_compute_market_state_skips_when_credit_missing() -> None:
    result = compute_market_state(
        {
            "risk_regime": _dimension_result("risk_regime", "risk_on"),
            "liquidity_regime": _dimension_result("liquidity_regime", "easy"),
            "inflation_regime": _dimension_result("inflation_regime", "stable"),
            "growth_regime": _dimension_result("growth_regime", "neutral"),
            "credit_regime": SignalResult(
                name="credit_regime",
                status="skipped",
                reason="missing_required_inputs",
            ),
        }
    )
    assert result.status == "skipped"
    assert "credit_regime" in result.inputs["missing"]
