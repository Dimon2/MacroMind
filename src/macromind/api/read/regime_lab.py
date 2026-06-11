from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any

from macromind.api.read.regime_cards import (
    credit_card,
    growth_card,
    inflation_card,
    latest_dp_from_signal_inputs,
    liquidity_card,
    risk_card,
)
from macromind.api.serializers import SCHEMA_VERSION
from macromind.db.signal_snapshot import rows_from_results
from macromind.signals.historical_feed import build_observations_as_of
from macromind.signals import regime_lab_cache as lab_cache
from macromind.signals.models import SignalResult
from macromind.signals.service import SignalService
from macromind.signals.stress_episodes import episode_for_date, list_episodes

LAB_MIN_DATE = date(1993, 1, 29)
WTREGEN_AVAILABLE_FROM = date(2008, 12, 18)

REGIME_SIGNAL_NAMES: tuple[str, ...] = (
    "risk_regime",
    "liquidity_regime",
    "inflation_regime",
    "growth_regime",
    "credit_regime",
    "market_state",
)


class InvalidQueryDateError(ValueError):
    pass


class FredApiKeyMissingError(RuntimeError):
    pass


def get_episodes() -> dict[str, Any]:
    return list_episodes()


def compute_regime_lab(query_date: date) -> dict[str, Any]:
    _validate_query_date(query_date)

    cached = lab_cache.get(query_date)
    if cached is not None:
        return cached

    try:
        observations = build_observations_as_of(query_date)
    except ValueError as exc:
        if "FRED_API_KEY" in str(exc):
            raise FredApiKeyMissingError(str(exc)) from exc
        raise

    service = SignalService()
    all_results = service.compute_results(observations)
    results = [r for r in all_results if r.name in REGIME_SIGNAL_NAMES]
    by_name_result = {r.name: r for r in results}

    rows = rows_from_results(query_date, results)
    by_name = {row.signal_name: row for row in rows}

    fetched_at = datetime.combine(query_date, time(23, 59, 59), tzinfo=timezone.utc)
    risk_result = by_name_result.get("risk_regime")
    credit_result = by_name_result.get("credit_regime")
    risk_inputs = dict(risk_result.inputs or {}) if risk_result else {}
    credit_inputs = dict(credit_result.inputs or {}) if credit_result else {}
    latest_dp = latest_dp_from_signal_inputs(risk_inputs, credit_inputs, fetched_at=fetched_at)

    market = by_name.get("market_state")
    composite = market.label if market and market.status == "computed" else None

    regime_computed = sum(1 for r in results if r.status == "computed")
    regime_skipped = sum(1 for r in results if r.status == "skipped")

    episode = episode_for_date(query_date)
    response: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "deterministic": True,
        "query_date": query_date.isoformat(),
        "episode": episode.to_dict() if episode is not None else None,
        "as_of": fetched_at.isoformat(),
        "composite": composite,
        "coverage": {
            "computed": regime_computed,
            "skipped": regime_skipped,
            "total": len(results),
        },
        "cards": {
            "risk": risk_card(by_name, latest_dp),
            "liquidity": liquidity_card(by_name),
            "inflation": inflation_card(by_name),
            "growth": growth_card(by_name, include_unrate=True),
            "credit": credit_card(by_name, latest_dp),
        },
        "signals": [r.to_dict() for r in results],
        "data_notes": _build_data_notes(query_date, results),
    }

    lab_cache.set(query_date, response)
    return response


def _validate_query_date(query_date: date) -> None:
    today = datetime.now(timezone.utc).date()
    if query_date < LAB_MIN_DATE:
        raise InvalidQueryDateError(
            f"query_date must be on or after {LAB_MIN_DATE.isoformat()} (SPY inception)"
        )
    if query_date > today:
        raise InvalidQueryDateError("query_date cannot be in the future")


def _build_data_notes(query_date: date, results: list[SignalResult]) -> list[str]:
    notes: list[str] = []
    if query_date < WTREGEN_AVAILABLE_FROM:
        notes.append(
            f"liquidity may be skipped: WTREGEN unavailable before {WTREGEN_AVAILABLE_FROM.isoformat()}"
        )
    notes.append(
        "growth_regime uses latest published UNRATE (monthly); may lag market stress on daily dates"
    )
    for result in results:
        if result.status == "skipped" and result.reason:
            notes.append(f"{result.name} skipped: {result.reason}")
    return notes
