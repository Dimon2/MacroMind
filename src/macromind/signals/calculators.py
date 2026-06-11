from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.models import SignalResult

# Net liquidity trend (WoW % on aligned WALCL − TGA − RRP)
NET_LIQUIDITY_EASY_PCT = 0.25
NET_LIQUIDITY_TIGHT_PCT = -0.25
LIQUIDITY_DRAIN_PCT = 1.0
RRP_BILLIONS_TO_MILLIONS = 1000.0

# Liquidity level (structural backdrop)
NET_LIQ_52W_WEEKS = 52
NET_LIQ_VS_52W_EASY_PCT = 3.0
NET_LIQ_VS_52W_TIGHT_PCT = -3.0
M2_YOY_LEVEL_EASY_PCT = 5.0
M2_YOY_LEVEL_TIGHT_PCT = 2.5
WALCL_26W_WEEKS = 26
WALCL_26W_EASY_PCT = 2.0
WALCL_26W_TIGHT_PCT = -2.0
DRAIN_26W_EASY_PCT = -5.0
DRAIN_26W_TIGHT_PCT = 5.0

# M2 YoY (monthly)
M2_YOY_LAG_MONTHS = 12
M2_MIN_POINTS_YOY = 13

# Inflation YoY on CPI index (13 monthly points)
CPI_YOY_LAG_MONTHS = 12
CPI_MIN_POINTS = 13
INFLATION_YOY_RISING_PCT = 3.5
INFLATION_YOY_FALLING_PCT = 2.5

# Growth (UNRATE Δ pp, curve; SPY optional context in inputs only)
GROWTH_UNRATE_EXPANDING_PP = -0.15
GROWTH_UNRATE_CONTRACTING_PP = 0.15

# Credit HY OAS spread (percent)
CREDIT_RELAXED_PCT = 3.5
CREDIT_STRESSED_PCT = 5.0

MARKET_STATE_DIMENSIONS: tuple[str, ...] = (
    "risk_regime",
    "liquidity_level_regime",
    "inflation_regime",
    "growth_regime",
    "credit_regime",
)

_NET_LIQUIDITY_SERIES = ("WALCL", "WTREGEN", "RRPONTSYD")


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
    elif vix_value >= 25:
        label = "risk_off"

    return SignalResult(
        name="risk_regime",
        status="computed",
        value=float(score),
        inputs={"SPY_change_pct": spy_change, "VIX": vix_value},
        metadata={"label": label},
        as_of=max(spy.fetched_at, vix.fetched_at),
    )


def compute_liquidity_trend_regime(observations: list[NormalizedObservation]) -> SignalResult:
    net_series = _compute_net_liquidity_series(observations)
    if len(net_series) < 2:
        return _skipped(
            name="liquidity_trend_regime",
            reason="insufficient_history",
            inputs={
                "required": "aligned WALCL, WTREGEN, RRPONTSYD",
                "aligned_points": len(net_series),
            },
        )

    latest_date, latest_net = net_series[0]
    prior_date, prior_net = net_series[1]
    net_chg = _pct_change(latest_net, prior_net)

    score = 0
    if net_chg is not None:
        if net_chg > NET_LIQUIDITY_EASY_PCT:
            score += 2
        elif net_chg < NET_LIQUIDITY_TIGHT_PCT:
            score -= 2

    as_of = _latest_as_of_for_series(observations, _NET_LIQUIDITY_SERIES)
    inputs: dict[str, object] = {
        "net_liquidity": latest_net,
        "net_liquidity_change_wow_pct": net_chg,
        "net_liquidity_date": latest_date.isoformat(),
        "net_liquidity_prior_date": prior_date.isoformat(),
    }
    inputs["components"] = _net_liquidity_components(observations, latest_date)

    for series_key in ("RRPONTSYD", "WTREGEN"):
        hist = _series_history(observations, series_key)
        if len(hist) < 2:
            continue
        chg = _pct_change(hist[0].value, hist[1].value)
        inputs[f"{series_key}_change_wow_pct"] = chg
        if chg is not None and chg > LIQUIDITY_DRAIN_PCT:
            score -= 1

    m2_inputs = _m2_overlay_inputs(observations)
    inputs.update(m2_inputs)

    label = _liquidity_easy_tight_label(score)

    return SignalResult(
        name="liquidity_trend_regime",
        status="computed",
        value=float(score),
        inputs=inputs,
        metadata={"label": label},
        as_of=as_of,
    )


def compute_liquidity_level_regime(observations: list[NormalizedObservation]) -> SignalResult:
    score = 0
    components_scored = 0
    inputs: dict[str, object] = {}

    net_series = _compute_net_liquidity_series(observations)
    if len(net_series) >= NET_LIQ_52W_WEEKS:
        window = net_series[:NET_LIQ_52W_WEEKS]
        values = [value for _, value in window]
        avg_52w = _rolling_mean(values)
        latest_net = values[0]
        vs_52w = _pct_vs_mean(latest_net, avg_52w)
        inputs["net_liquidity_vs_52w_pct"] = vs_52w
        inputs["net_liquidity_52w_avg"] = avg_52w
        inputs["net_liquidity_vs_52w_status"] = "computed"
        components_scored += 1
        if vs_52w is not None:
            if vs_52w > NET_LIQ_VS_52W_EASY_PCT:
                score += 1
            elif vs_52w < NET_LIQ_VS_52W_TIGHT_PCT:
                score -= 1
    else:
        inputs["net_liquidity_vs_52w_status"] = "insufficient"
        inputs["net_liquidity_vs_52w_pct"] = None
        inputs["net_liquidity_52w_avg"] = None

    m2_inputs = _m2_overlay_inputs(observations)
    inputs.update(m2_inputs)
    m2_yoy = m2_inputs.get("M2SL_yoy_pct")
    if m2_inputs.get("M2SL_yoy_status") == "computed" and m2_yoy is not None:
        components_scored += 1
        if float(m2_yoy) > M2_YOY_LEVEL_EASY_PCT:
            score += 1
        elif float(m2_yoy) < M2_YOY_LEVEL_TIGHT_PCT:
            score -= 1

    walcl_chg = _walcl_change_weeks(observations, weeks=WALCL_26W_WEEKS)
    if walcl_chg is not None:
        inputs["WALCL_change_26w_pct"] = walcl_chg
        inputs["WALCL_change_26w_status"] = "computed"
        components_scored += 1
        if walcl_chg > WALCL_26W_EASY_PCT:
            score += 1
        elif walcl_chg < WALCL_26W_TIGHT_PCT:
            score -= 1
    else:
        inputs["WALCL_change_26w_pct"] = None
        inputs["WALCL_change_26w_status"] = "insufficient"

    drain_chg = _drain_change_weeks(observations, weeks=WALCL_26W_WEEKS)
    if drain_chg is not None:
        inputs["drain_change_26w_pct"] = drain_chg
        inputs["drain_change_26w_status"] = "computed"
        components_scored += 1
        if drain_chg < DRAIN_26W_EASY_PCT:
            score += 1
        elif drain_chg > DRAIN_26W_TIGHT_PCT:
            score -= 1
    else:
        inputs["drain_change_26w_pct"] = None
        inputs["drain_change_26w_status"] = "insufficient"

    inputs["components_scored"] = components_scored
    inputs["components_total"] = 4

    if components_scored == 0:
        return _skipped(
            name="liquidity_level_regime",
            reason="insufficient_history",
            inputs=inputs,
        )

    as_of = _latest_as_of_for_series(observations, _NET_LIQUIDITY_SERIES + ("M2SL", "WALCL"))
    label = _liquidity_easy_tight_label(score)

    return SignalResult(
        name="liquidity_level_regime",
        status="computed",
        value=float(score),
        inputs=inputs,
        metadata={"label": label},
        as_of=as_of,
    )


def compute_credit_regime(observations: list[NormalizedObservation]) -> SignalResult:
    by_key = _latest_by_series_key(observations)
    spread_obs = by_key.get("BAMLH0A0HYM2")
    if spread_obs is None:
        return _skipped(
            name="credit_regime",
            reason="missing_required_inputs",
            inputs={"required": ["BAMLH0A0HYM2"], "available": sorted(by_key.keys())},
        )

    spread = spread_obs.value
    if spread < CREDIT_RELAXED_PCT:
        label = "relaxed"
    elif spread > CREDIT_STRESSED_PCT:
        label = "stressed"
    else:
        label = "normal"

    inputs: dict[str, object] = {"BAMLH0A0HYM2": spread}
    hyg = by_key.get("HYG")
    if hyg is not None:
        inputs["HYG_change_pct"] = _to_float(hyg.metadata.get("change_pct"))
        as_of = max(spread_obs.fetched_at, hyg.fetched_at)
    else:
        as_of = spread_obs.fetched_at

    return SignalResult(
        name="credit_regime",
        status="computed",
        value=spread,
        inputs=inputs,
        metadata={"label": label},
        as_of=as_of,
    )


def compute_inflation_regime(observations: list[NormalizedObservation]) -> SignalResult:
    headline_hist = _series_history(observations, "CPIAUCSL")
    core_hist = _series_history(observations, "CPILFESL")
    counts = {"CPIAUCSL": len(headline_hist), "CPILFESL": len(core_hist)}
    headline_yoy = _yoy_percent(headline_hist, lag=CPI_YOY_LAG_MONTHS)

    if headline_yoy is None:
        return _skipped(
            name="inflation_regime",
            reason="insufficient_history",
            inputs={
                "required_series": "CPIAUCSL",
                "required_points": CPI_MIN_POINTS,
                "lag_months": CPI_YOY_LAG_MONTHS,
                "points": counts,
            },
        )

    inputs: dict[str, object] = {"headline_yoy_pct": headline_yoy}
    core_yoy = _yoy_percent(core_hist, lag=CPI_YOY_LAG_MONTHS)
    if core_yoy is not None:
        inputs["core_yoy_pct"] = core_yoy

    as_of = headline_hist[0].fetched_at
    if core_hist and core_yoy is not None:
        as_of = max(as_of, core_hist[0].fetched_at)

    if headline_yoy > INFLATION_YOY_RISING_PCT:
        label = "rising"
    elif headline_yoy < INFLATION_YOY_FALLING_PCT:
        label = "falling"
    else:
        label = "stable"

    return SignalResult(
        name="inflation_regime",
        status="computed",
        value=float(headline_yoy),
        inputs=inputs,
        metadata={"label": label},
        as_of=as_of,
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

    curve = _curve_context(observations)
    if curve is not None:
        curve_as_of = curve.pop("curve_as_of", None)
        inputs.update(curve)
        if isinstance(curve_as_of, datetime):
            as_of = max(as_of, curve_as_of)
        curve_state = curve.get("curve_state")
        if curve_state == "inverted":
            score -= 1
        else:
            score += 1

    by_key = _latest_by_series_key(observations)
    spy = by_key.get("SPY")
    if spy is not None:
        inputs["SPY_change_pct"] = _to_float(spy.metadata.get("change_pct"))

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

    composite = "_".join(labels[name] for name in MARKET_STATE_DIMENSIONS)
    as_of = max(dimension_results[name].as_of for name in MARKET_STATE_DIMENSIONS)

    return SignalResult(
        name="market_state",
        status="computed",
        value=None,
        inputs={"dimensions": labels},
        metadata={"label": composite},
        as_of=as_of,
    )


def _curve_context(observations: list[NormalizedObservation]) -> dict[str, Any] | None:
    by_key = _latest_by_series_key(observations)
    t10y2y = by_key.get("T10Y2Y")
    if t10y2y is not None:
        spread = t10y2y.value
        as_of = t10y2y.fetched_at
        source = "T10Y2Y"
    else:
        dgs10 = by_key.get("DGS10")
        dgs2 = by_key.get("DGS2")
        if dgs10 is None or dgs2 is None:
            return None
        spread = dgs10.value - dgs2.value
        as_of = max(dgs10.fetched_at, dgs2.fetched_at)
        source = "DGS10-DGS2"

    return {
        "curve_spread": float(spread),
        "curve_state": "inverted" if spread < 0 else "normal",
        "curve_source": source,
        "curve_as_of": as_of,
    }


def _compute_net_liquidity_series(
    observations: list[NormalizedObservation],
) -> list[tuple[date, float]]:
    by_series: dict[str, dict[date, float]] = {}
    for series_key in _NET_LIQUIDITY_SERIES:
        hist = _series_history(observations, series_key)
        by_series[series_key] = {obs.observation_date: obs.value for obs in hist}

    common_dates = set(by_series["WALCL"]) & set(by_series["WTREGEN"]) & set(by_series["RRPONTSYD"])
    if not common_dates:
        return []

    net_levels: list[tuple[date, float]] = []
    for obs_date in common_dates:
        walcl = by_series["WALCL"][obs_date]
        tga = by_series["WTREGEN"][obs_date]
        rrp_millions = by_series["RRPONTSYD"][obs_date] * RRP_BILLIONS_TO_MILLIONS
        net_levels.append((obs_date, walcl - tga - rrp_millions))

    return sorted(net_levels, key=lambda item: item[0], reverse=True)


def _net_liquidity_components(
    observations: list[NormalizedObservation],
    obs_date: date,
) -> dict[str, float]:
    components: dict[str, float] = {}
    for series_key in _NET_LIQUIDITY_SERIES:
        hist = _series_history(observations, series_key)
        for obs in hist:
            if obs.observation_date == obs_date:
                components[series_key] = obs.value
                break
    if "RRPONTSYD" in components:
        components["RRPONTSYD_millions"] = (
            components["RRPONTSYD"] * RRP_BILLIONS_TO_MILLIONS
        )
    return components


def _liquidity_easy_tight_label(score: int) -> str:
    if score >= 2:
        return "easy"
    if score <= -2:
        return "tight"
    return "neutral"


def _rolling_mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _pct_vs_mean(latest: float, mean: float) -> float | None:
    if mean == 0:
        return None
    return (latest - mean) / mean * 100.0


def _walcl_change_weeks(
    observations: list[NormalizedObservation],
    *,
    weeks: int,
) -> float | None:
    hist = _series_history(observations, "WALCL")
    if len(hist) <= weeks:
        return None
    return _pct_change(hist[0].value, hist[weeks].value)


def _drain_change_weeks(
    observations: list[NormalizedObservation],
    *,
    weeks: int,
) -> float | None:
    by_series: dict[str, dict[date, float]] = {}
    for series_key in ("WTREGEN", "RRPONTSYD"):
        hist = _series_history(observations, series_key)
        by_series[series_key] = {obs.observation_date: obs.value for obs in hist}

    common_dates = set(by_series["WTREGEN"]) & set(by_series["RRPONTSYD"])
    if not common_dates:
        return None

    drain_levels: list[tuple[date, float]] = []
    for obs_date in common_dates:
        tga = by_series["WTREGEN"][obs_date]
        rrp_millions = by_series["RRPONTSYD"][obs_date] * RRP_BILLIONS_TO_MILLIONS
        drain_levels.append((obs_date, tga + rrp_millions))

    drain_series = sorted(drain_levels, key=lambda item: item[0], reverse=True)
    if len(drain_series) <= weeks:
        return None
    latest_drain = drain_series[0][1]
    prior_drain = drain_series[weeks][1]
    return _pct_change(latest_drain, prior_drain)


def _m2_overlay_inputs(observations: list[NormalizedObservation]) -> dict[str, object]:
    hist = _series_history(observations, "M2SL")
    if not hist:
        return {"M2SL_yoy_status": "missing"}

    latest = hist[0]
    inputs: dict[str, object] = {
        "M2SL_latest": latest.value,
        "M2SL_latest_date": latest.observation_date.isoformat(),
    }

    if len(hist) >= 2:
        inputs["M2SL_change_mom_pct"] = _pct_change(hist[0].value, hist[1].value)
    else:
        inputs["M2SL_change_mom_pct"] = None

    yoy = _yoy_percent(hist, lag=M2_YOY_LAG_MONTHS)
    if yoy is not None:
        inputs["M2SL_yoy_pct"] = yoy
        inputs["M2SL_yoy_status"] = "computed"
    else:
        inputs["M2SL_yoy_pct"] = None
        inputs["M2SL_yoy_status"] = "insufficient_history"

    return inputs


def _latest_as_of_for_series(
    observations: list[NormalizedObservation],
    series_keys: tuple[str, ...],
) -> datetime:
    latest = datetime.min.replace(tzinfo=timezone.utc)
    by_key = _latest_by_series_key(observations)
    for key in series_keys:
        obs = by_key.get(key)
        if obs is not None:
            latest = max(latest, obs.fetched_at)
    if latest == datetime.min.replace(tzinfo=timezone.utc):
        return datetime.now(timezone.utc)
    return latest


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
