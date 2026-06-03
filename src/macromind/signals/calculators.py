from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.models import SignalResult

# Liquidity (WALCL WoW %, RRP/TGA drain)
LIQUIDITY_WALCL_EASY_PCT = 0.25
LIQUIDITY_WALCL_TIGHT_PCT = -0.25
LIQUIDITY_DRAIN_PCT = 1.0

# Inflation YoY on CPI index (13 monthly points)
CPI_YOY_LAG_MONTHS = 12
CPI_MIN_POINTS = 13
INFLATION_YOY_RISING_PCT = 3.5
INFLATION_YOY_FALLING_PCT = 2.5

# Growth (UNRATE Δ pp, curve, optional SPY)
GROWTH_UNRATE_EXPANDING_PP = -0.05
GROWTH_UNRATE_CONTRACTING_PP = 0.05

MARKET_STATE_DIMENSIONS: tuple[str, ...] = (
    "risk_regime",
    "liquidity_regime",
    "inflation_regime",
    "growth_regime",
)


def compute_risk_regime(observations: list[NormalizedObservation]) -> SignalResult:
    by_key = _latest_by_series_key(observations)
    spy = by_key.get("SPY")
    vix = by_key.get("VIX")
    if spy is None or vix is None:
        return _skipped(
            name="risk_regime",
            reason="missing_required_inputs",
            inputs={"required": ["SPY", "VIX"], "available": sorted(by_key.keys())},
        )

    spy_change = _to_float(spy.metadata.get("change_pct"))
    vix_value = vix.value
    score = 0
    if spy_change is not None:
        if spy_change > 0:
            score += 1
        elif spy_change < 0:
            score -= 1
    if vix_value <= 20:
        score += 1
    elif vix_value >= 25:
        score -= 1

    label = "neutral"
    if score > 0:
        label = "risk_on"
    elif score < 0:
        label = "risk_off"

    return SignalResult(
        name="risk_regime",
        status="computed",
        value=float(score),
        inputs={"SPY_change_pct": spy_change, "VIX": vix_value},
        metadata={"label": label},
        as_of=max(spy.fetched_at, vix.fetched_at),
    )


def compute_rates_curve_proxy(observations: list[NormalizedObservation]) -> SignalResult:
    by_key = _latest_by_series_key(observations)
    t10y2y = by_key.get("T10Y2Y")
    if t10y2y is not None:
        spread = t10y2y.value
        as_of = t10y2y.fetched_at
        inputs = {"T10Y2Y": spread}
    else:
        dgs10 = by_key.get("DGS10")
        dgs2 = by_key.get("DGS2")
        if dgs10 is None or dgs2 is None:
            return _skipped(
                name="rates_curve_proxy",
                reason="missing_required_inputs",
                inputs={"required": ["T10Y2Y or (DGS10 and DGS2)"]},
            )
        spread = dgs10.value - dgs2.value
        as_of = max(dgs10.fetched_at, dgs2.fetched_at)
        inputs = {"DGS10": dgs10.value, "DGS2": dgs2.value}

    return SignalResult(
        name="rates_curve_proxy",
        status="computed",
        value=float(spread),
        inputs=inputs,
        metadata={"curve_state": "inverted" if spread < 0 else "normal"},
        as_of=as_of,
    )


def compute_macro_implied_inflation_prob(
    observations: list[NormalizedObservation],
) -> SignalResult:
    inflation = [
        obs
        for obs in observations
        if obs.value_kind == "probability" and str(obs.metadata.get("macro_topic", "")).lower() == "inflation"
    ]
    if not inflation:
        return _skipped(
            name="macro_implied_inflation_prob",
            reason="missing_required_inputs",
            inputs={"required": ["probability observations with macro_topic=inflation"]},
        )

    latest_obs = max(inflation, key=lambda item: (item.observation_date, item.fetched_at))
    values = [item.value for item in inflation]
    return SignalResult(
        name="macro_implied_inflation_prob",
        status="computed",
        value=float(mean(values)),
        inputs={"markets_count": len(values), "latest_market": latest_obs.series_key},
        metadata={
            "latest_value": latest_obs.value,
            "latest_observation_date": latest_obs.observation_date.isoformat(),
        },
        as_of=latest_obs.fetched_at,
    )


def compute_liquidity_regime(observations: list[NormalizedObservation]) -> SignalResult:
    walcl_hist = _series_history(observations, "WALCL")
    if len(walcl_hist) < 2:
        return _skipped(
            name="liquidity_regime",
            reason="insufficient_history",
            inputs={
                "required_series": "WALCL",
                "required_points": 2,
                "points": len(walcl_hist),
            },
        )

    score = 0
    walcl_chg = _pct_change(walcl_hist[0].value, walcl_hist[1].value)
    inputs: dict[str, object] = {
        "WALCL_change_pct": walcl_chg,
        "WALCL_latest_date": walcl_hist[0].observation_date.isoformat(),
    }

    if walcl_chg is not None:
        if walcl_chg > LIQUIDITY_WALCL_EASY_PCT:
            score += 2
        elif walcl_chg < LIQUIDITY_WALCL_TIGHT_PCT:
            score -= 2

    as_of = walcl_hist[0].fetched_at
    for series_key in ("RRPONTSYD", "WTREGEN"):
        hist = _series_history(observations, series_key)
        if len(hist) < 2:
            continue
        chg = _pct_change(hist[0].value, hist[1].value)
        inputs[f"{series_key}_change_pct"] = chg
        as_of = max(as_of, hist[0].fetched_at)
        if chg is not None and chg > LIQUIDITY_DRAIN_PCT:
            score -= 1

    label = "neutral"
    if score >= 2:
        label = "easy"
    elif score <= -2:
        label = "tight"

    return SignalResult(
        name="liquidity_regime",
        status="computed",
        value=float(score),
        inputs=inputs,
        metadata={"label": label},
        as_of=as_of,
    )


def compute_inflation_regime(observations: list[NormalizedObservation]) -> SignalResult:
    yoy_by_series: dict[str, float] = {}
    counts: dict[str, int] = {}
    latest_as_of = datetime.now(timezone.utc)

    for series_key in ("CPIAUCSL", "CPILFESL"):
        hist = _series_history(observations, series_key)
        counts[series_key] = len(hist)
        yoy = _yoy_percent(hist, lag=CPI_YOY_LAG_MONTHS)
        if yoy is not None:
            yoy_by_series[series_key] = yoy
            latest_as_of = max(latest_as_of, hist[0].fetched_at)

    if not yoy_by_series:
        return _skipped(
            name="inflation_regime",
            reason="insufficient_history",
            inputs={
                "required_points": CPI_MIN_POINTS,
                "lag_months": CPI_YOY_LAG_MONTHS,
                "points": counts,
            },
        )

    avg_yoy = float(mean(yoy_by_series.values()))
    if avg_yoy > INFLATION_YOY_RISING_PCT:
        label = "rising"
    elif avg_yoy < INFLATION_YOY_FALLING_PCT:
        label = "falling"
    else:
        label = "stable"

    return SignalResult(
        name="inflation_regime",
        status="computed",
        value=avg_yoy,
        inputs={"yoy_pct_by_series": yoy_by_series},
        metadata={"label": label},
        as_of=latest_as_of,
    )


def compute_growth_regime(observations: list[NormalizedObservation]) -> SignalResult:
    unrate_hist = _series_history(observations, "UNRATE")
    if len(unrate_hist) < 2:
        return _skipped(
            name="growth_regime",
            reason="insufficient_history",
            inputs={
                "required_series": "UNRATE",
                "required_points": 2,
                "points": len(unrate_hist),
            },
        )

    unrate_delta = unrate_hist[0].value - unrate_hist[1].value
    score = 0
    if unrate_delta < GROWTH_UNRATE_EXPANDING_PP:
        score += 2
    elif unrate_delta > GROWTH_UNRATE_CONTRACTING_PP:
        score -= 2

    inputs: dict[str, object] = {
        "UNRATE_delta_pp": unrate_delta,
        "UNRATE_latest": unrate_hist[0].value,
        "UNRATE_prior": unrate_hist[1].value,
    }
    as_of = unrate_hist[0].fetched_at

    curve = compute_rates_curve_proxy(observations)
    if curve.status == "computed":
        curve_state = curve.metadata.get("curve_state")
        inputs["curve_state"] = curve_state
        inputs["curve_spread"] = curve.value
        as_of = max(as_of, curve.as_of)
        if curve_state == "inverted":
            score -= 1
        else:
            score += 1

    by_key = _latest_by_series_key(observations)
    spy = by_key.get("SPY")
    if spy is not None:
        spy_change = _to_float(spy.metadata.get("change_pct"))
        inputs["SPY_change_pct"] = spy_change
        as_of = max(as_of, spy.fetched_at)
        if spy_change is not None:
            if spy_change > 0:
                score += 1
            elif spy_change < 0:
                score -= 1

    label = "neutral"
    if score >= 2:
        label = "expanding"
    elif score <= -2:
        label = "contracting"

    return SignalResult(
        name="growth_regime",
        status="computed",
        value=float(score),
        inputs=inputs,
        metadata={"label": label},
        as_of=as_of,
    )


def compute_market_state(dimension_results: dict[str, SignalResult]) -> SignalResult:
    labels: dict[str, str] = {}
    missing: list[str] = []

    for name in MARKET_STATE_DIMENSIONS:
        result = dimension_results.get(name)
        if result is None or result.status != "computed":
            missing.append(name)
            continue
        label = result.metadata.get("label")
        if label is None:
            missing.append(name)
            continue
        labels[name] = str(label)

    if missing:
        return _skipped(
            name="market_state",
            reason="missing_dimension_labels",
            inputs={"missing": missing, "computed_dimensions": labels},
        )

    composite = (
        f"{labels['risk_regime']}_{labels['liquidity_regime']}_"
        f"{labels['inflation_regime']}_{labels['growth_regime']}"
    )
    as_of = max(dimension_results[name].as_of for name in MARKET_STATE_DIMENSIONS)

    return SignalResult(
        name="market_state",
        status="computed",
        value=None,
        inputs={"dimensions": labels},
        metadata={"label": composite},
        as_of=as_of,
    )


def _latest_by_series_key(
    observations: list[NormalizedObservation],
) -> dict[str, NormalizedObservation]:
    latest: dict[str, NormalizedObservation] = {}
    for obs in observations:
        current = latest.get(obs.series_key)
        if current is None or (obs.observation_date, obs.fetched_at) > (
            current.observation_date,
            current.fetched_at,
        ):
            latest[obs.series_key] = obs
    return latest


def _series_history(
    observations: list[NormalizedObservation],
    series_key: str,
) -> list[NormalizedObservation]:
    rows = [obs for obs in observations if obs.series_key == series_key]
    return sorted(rows, key=lambda item: (item.observation_date, item.fetched_at), reverse=True)


def _pct_change(latest: float, prior: float) -> float | None:
    if prior == 0:
        return None
    return (latest - prior) / prior * 100.0


def _yoy_percent(
    history: list[NormalizedObservation],
    *,
    lag: int,
) -> float | None:
    if len(history) <= lag:
        return None
    return _pct_change(history[0].value, history[lag].value)


def _skipped(name: str, reason: str, inputs: dict[str, object] | None = None) -> SignalResult:
    return SignalResult(
        name=name,
        status="skipped",
        value=None,
        reason=reason,
        inputs=inputs or {},
        as_of=datetime.now(timezone.utc),
    )


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
