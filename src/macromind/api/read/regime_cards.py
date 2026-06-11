from __future__ import annotations

from typing import Any

from macromind.db.signal_snapshot import SignalSnapshotRow
from macromind.market.normalized_observation import NormalizedObservation
from macromind.models import DataPoint


def regime_block(row: SignalSnapshotRow | None) -> dict[str, Any]:
    if row is None:
        return {"status": "missing", "label": None, "value": None}
    return {
        "status": row.status,
        "label": row.label,
        "value": row.value,
        "reason": row.reason,
        "as_of": row.as_of.isoformat(),
    }


def risk_card(
    by_name: dict[str, SignalSnapshotRow],
    latest_dp: dict[str, Any],
) -> dict[str, Any]:
    series: dict[str, Any] = {}
    spy = latest_dp.get("SPY")
    if spy is not None:
        series["SPY"] = {
            "value": spy.value,
            "change_pct": (spy.metadata or {}).get("change_pct"),
        }
    vix = latest_dp.get("VIX")
    if vix is not None:
        series["VIX"] = {"value": vix.value}
    return {"regime": regime_block(by_name.get("risk_regime")), "series": series}


def liquidity_card(by_name: dict[str, SignalSnapshotRow]) -> dict[str, Any]:
    level_row = by_name.get("liquidity_level_regime")
    trend_row = by_name.get("liquidity_trend_regime")
    context_row = by_name.get("liquidity_context")

    trend_inputs = dict(trend_row.inputs) if trend_row else {}
    level_inputs_raw = dict(level_row.inputs) if level_row else {}

    net_liquidity: dict[str, Any] = {
        "level_millions": trend_inputs.get("net_liquidity"),
        "change_wow_pct": trend_inputs.get("net_liquidity_change_wow_pct"),
        "as_of": trend_inputs.get("net_liquidity_date"),
    }
    m2: dict[str, Any] = {
        "level_billions": trend_inputs.get("M2SL_latest") or level_inputs_raw.get("M2SL_latest"),
        "change_mom_pct": trend_inputs.get("M2SL_change_mom_pct")
        or level_inputs_raw.get("M2SL_change_mom_pct"),
        "yoy_pct": trend_inputs.get("M2SL_yoy_pct") or level_inputs_raw.get("M2SL_yoy_pct"),
        "yoy_status": trend_inputs.get("M2SL_yoy_status")
        or level_inputs_raw.get("M2SL_yoy_status"),
    }
    level_inputs: dict[str, Any] = {
        "vs_52w_pct": level_inputs_raw.get("net_liquidity_vs_52w_pct"),
        "walcl_26w_pct": level_inputs_raw.get("WALCL_change_26w_pct"),
        "drain_26w_pct": level_inputs_raw.get("drain_change_26w_pct"),
        "components_scored": level_inputs_raw.get("components_scored"),
        "components_total": level_inputs_raw.get("components_total"),
    }
    matrix: dict[str, Any] = {"key": None, "interpretation": None}
    if context_row and context_row.status == "computed":
        ctx_inputs = dict(context_row.inputs) if context_row.inputs else {}
        matrix = {
            "key": context_row.label,
            "interpretation": ctx_inputs.get("interpretation"),
        }

    return {
        "regime": regime_block(level_row),
        "level": regime_block(level_row),
        "trend": regime_block(trend_row),
        "matrix": matrix,
        "net_liquidity": net_liquidity,
        "level_inputs": level_inputs,
        "m2": m2,
        "series_keys": ["WALCL", "WTREGEN", "RRPONTSYD", "M2SL"],
    }


def inflation_card(by_name: dict[str, SignalSnapshotRow]) -> dict[str, Any]:
    row = by_name.get("inflation_regime")
    inputs = dict(row.inputs) if row else {}
    return {
        "regime": regime_block(row),
        "headline_yoy_pct": inputs.get("headline_yoy_pct"),
        "core_yoy_pct": inputs.get("core_yoy_pct"),
        "series_keys": ["CPIAUCSL", "CPILFESL"],
    }


def growth_card(
    by_name: dict[str, SignalSnapshotRow],
    *,
    include_unrate: bool = False,
) -> dict[str, Any]:
    row = by_name.get("growth_regime")
    inputs = dict(row.inputs) if row else {}
    curve = {
        "curve_spread": inputs.get("curve_spread"),
        "curve_state": inputs.get("curve_state"),
        "curve_source": inputs.get("curve_source"),
    }
    card: dict[str, Any] = {
        "regime": regime_block(row),
        "curve": curve,
        "series_keys": ["UNRATE"],
    }
    if include_unrate:
        card["unrate"] = {
            "latest": inputs.get("UNRATE_latest"),
            "prior": inputs.get("UNRATE_prior"),
            "delta_pp": inputs.get("UNRATE_delta_pp"),
        }
    return card


def credit_card(
    by_name: dict[str, SignalSnapshotRow],
    latest_dp: dict[str, Any],
) -> dict[str, Any]:
    row = by_name.get("credit_regime")
    series: dict[str, Any] = {}
    baml = latest_dp.get("BAMLH0A0HYM2")
    if baml is not None:
        series["BAMLH0A0HYM2"] = {"value": baml.value}
    hyg = latest_dp.get("HYG")
    if hyg is not None:
        series["HYG"] = {
            "value": hyg.value,
            "change_pct": (hyg.metadata or {}).get("change_pct"),
        }
    return {"regime": regime_block(row), "series": series}


def latest_dp_from_signal_inputs(
    risk_inputs: dict[str, Any],
    credit_inputs: dict[str, Any],
    *,
    fetched_at: Any,
) -> dict[str, DataPoint]:
    latest: dict[str, DataPoint] = {}
    vix = risk_inputs.get("VIX")
    if vix is not None:
        latest["VIX"] = DataPoint(
            source="yfinance",
            indicator="VIX",
            value=float(vix),
            unit="index",
            period="",
            fetched_at=fetched_at,
            metadata={},
        )
    spy_chg = risk_inputs.get("SPY_change_pct")
    if spy_chg is not None:
        latest["SPY"] = DataPoint(
            source="yfinance",
            indicator="SPY",
            value=0.0,
            unit="usd",
            period="",
            fetched_at=fetched_at,
            metadata={"change_pct": spy_chg},
        )
    spread = credit_inputs.get("BAMLH0A0HYM2")
    if spread is not None:
        latest["BAMLH0A0HYM2"] = DataPoint(
            source="fred",
            indicator="BAMLH0A0HYM2",
            value=float(spread),
            unit="percent",
            period="",
            fetched_at=fetched_at,
            metadata={},
        )
    hyg_chg = credit_inputs.get("HYG_change_pct")
    if hyg_chg is not None:
        latest["HYG"] = DataPoint(
            source="yfinance",
            indicator="HYG",
            value=0.0,
            unit="usd",
            period="",
            fetched_at=fetched_at,
            metadata={"change_pct": hyg_chg},
        )
    return latest


def merge_market_datapoints(
    latest_dp: dict[str, DataPoint],
    observations: list[NormalizedObservation],
) -> dict[str, DataPoint]:
    merged = dict(latest_dp)
    market_keys = ("SPY", "VIX", "HYG", "BAMLH0A0HYM2")
    best: dict[str, NormalizedObservation] = {}
    for obs in observations:
        if obs.series_key not in market_keys:
            continue
        current = best.get(obs.series_key)
        if current is None or (obs.observation_date, obs.fetched_at) > (
            current.observation_date,
            current.fetched_at,
        ):
            best[obs.series_key] = obs

    for key, obs in best.items():
        metadata = dict(obs.metadata or {})
        if key in ("SPY", "HYG"):
            existing = merged.get(key)
            if existing is not None:
                metadata.setdefault("change_pct", (existing.metadata or {}).get("change_pct"))
        merged[key] = DataPoint(
            source=obs.source,
            indicator=obs.series_key,
            value=obs.value,
            unit=obs.unit,
            period=obs.observation_date.isoformat(),
            fetched_at=obs.fetched_at,
            metadata=metadata,
        )
    return merged
