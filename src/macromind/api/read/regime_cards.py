from __future__ import annotations

from typing import Any

from macromind.db.signal_snapshot import SignalSnapshotRow
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
    row = by_name.get("liquidity_regime")
    inputs = dict(row.inputs) if row else {}
    net_liquidity: dict[str, Any] = {
        "level_millions": inputs.get("net_liquidity"),
        "change_wow_pct": inputs.get("net_liquidity_change_wow_pct"),
        "as_of": inputs.get("net_liquidity_date"),
    }
    m2: dict[str, Any] = {
        "level_billions": inputs.get("M2SL_latest"),
        "change_mom_pct": inputs.get("M2SL_change_mom_pct"),
        "yoy_pct": inputs.get("M2SL_yoy_pct"),
        "yoy_status": inputs.get("M2SL_yoy_status"),
    }
    return {
        "regime": regime_block(row),
        "net_liquidity": net_liquidity,
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
