from __future__ import annotations

from typing import Any

from macromind.db.repository import MacroRepository
from macromind.db.signal_snapshot import SignalSnapshotRepository, SignalSnapshotRow
from macromind.signals.delta import build_deltas

from macromind.api.read.regime_cards import (
    credit_card,
    growth_card,
    inflation_card,
    liquidity_card,
    risk_card,
)
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
            "risk": risk_card(by_name, latest_dp),
            "liquidity": liquidity_card(by_name),
            "inflation": inflation_card(by_name),
            "growth": growth_card(by_name),
            "credit": credit_card(by_name, latest_dp),
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
