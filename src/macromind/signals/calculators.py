from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.models import SignalResult


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
