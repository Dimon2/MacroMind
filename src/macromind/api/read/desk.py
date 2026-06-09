from __future__ import annotations

from typing import Any

from macromind.db.repository import MacroRepository
from macromind.db.signal_snapshot import SignalSnapshotRepository, SignalSnapshotRow
from macromind.signals.delta import build_deltas

from macromind.api.serializers import SCHEMA_VERSION, snapshot_row_to_signal_dict


class NoSnapshotsError(Exception):
    pass


def load_latest_desk(
    *,
    snapshot_repo: SignalSnapshotRepository | None = None,
    macro_repo: MacroRepository | None = None,
) -> dict[str, Any]:
    repo = snapshot_repo or SignalSnapshotRepository()
    macro = macro_repo or MacroRepository()
    rows = repo.load_latest_snapshots()
    if not rows:
        raise NoSnapshotsError()

    by_name = {row.signal_name: row for row in rows}
    snapshot_date = rows[0].snapshot_date
    prev_date, deltas = build_deltas(rows, repo)
    as_of = max(row.as_of for row in rows).isoformat()
    market = by_name.get("market_state")
    composite = market.label if market and market.status == "computed" else None

    latest_dp = {dp.indicator: dp for dp in macro.load_latest_datapoints()}

    return {
        "schema_version": SCHEMA_VERSION,
        "deterministic": True,
        "snapshot_date": snapshot_date.isoformat(),
        "as_of": as_of,
        "composite": composite,
        "cards": {
            "risk": _risk_card(by_name, latest_dp),
            "liquidity": _liquidity_card(by_name),
            "inflation": _inflation_card(by_name),
            "growth": _growth_card(by_name),
            "credit": _credit_card(by_name, latest_dp),
        },
        "overlays": {
            "inflation_pm": _inflation_pm_overlay(by_name),
            "fed_compare": _fed_compare_overlay(by_name),
        },
        "deltas": [delta.to_dict() for delta in deltas],
        "previous_snapshot_date": prev_date.isoformat() if prev_date else None,
        "details": {
            "signals": [snapshot_row_to_signal_dict(row) for row in rows],
        },
    }


def _regime_block(row: SignalSnapshotRow | None) -> dict[str, Any]:
    if row is None:
        return {"status": "missing", "label": None, "value": None}
    return {
        "status": row.status,
        "label": row.label,
        "value": row.value,
        "reason": row.reason,
        "as_of": row.as_of.isoformat(),
    }


def _risk_card(
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
    return {"regime": _regime_block(by_name.get("risk_regime")), "series": series}


def _liquidity_card(by_name: dict[str, SignalSnapshotRow]) -> dict[str, Any]:
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
        "regime": _regime_block(row),
        "net_liquidity": net_liquidity,
        "m2": m2,
        "series_keys": ["WALCL", "WTREGEN", "RRPONTSYD", "M2SL"],
    }


def _inflation_card(by_name: dict[str, SignalSnapshotRow]) -> dict[str, Any]:
    row = by_name.get("inflation_regime")
    inputs = dict(row.inputs) if row else {}
    return {
        "regime": _regime_block(row),
        "headline_yoy_pct": inputs.get("headline_yoy_pct"),
        "core_yoy_pct": inputs.get("core_yoy_pct"),
        "series_keys": ["CPIAUCSL", "CPILFESL"],
    }


def _growth_card(by_name: dict[str, SignalSnapshotRow]) -> dict[str, Any]:
    row = by_name.get("growth_regime")
    inputs = dict(row.inputs) if row else {}
    curve = {
        "curve_spread": inputs.get("curve_spread"),
        "curve_state": inputs.get("curve_state"),
        "curve_source": inputs.get("curve_source"),
    }
    return {
        "regime": _regime_block(row),
        "curve": curve,
        "series_keys": ["UNRATE"],
    }


def _credit_card(
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
    return {"regime": _regime_block(row), "series": series}


def _inflation_pm_overlay(by_name: dict[str, SignalSnapshotRow]) -> dict[str, Any]:
    row = by_name.get("inflation_pm_overlay")
    if row is None or row.status != "computed":
        return {"markets": [], "status": row.status if row else "missing", "reason": row.reason if row else None}
    return {"markets": list(row.inputs.get("markets") or []), "status": "computed"}


def _fed_compare_overlay(by_name: dict[str, SignalSnapshotRow]) -> dict[str, Any]:
    row = by_name.get("fed_rate_context")
    if row is None or row.status != "computed":
        return {
            "effective_rate": None,
            "kalshi_markets": [],
            "status": row.status if row else "missing",
            "reason": row.reason if row else None,
        }
    return {
        "effective_rate": row.inputs.get("effective_rate"),
        "unit": row.inputs.get("unit"),
        "kalshi_markets": list(row.inputs.get("kalshi_markets") or []),
        "status": "computed",
    }
