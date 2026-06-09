from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.models import SignalResult


def build_inflation_pm_overlay(observations: list[NormalizedObservation]) -> SignalResult:
    inflation = [
        obs
        for obs in observations
        if obs.value_kind == "probability"
        and str(obs.metadata.get("macro_topic", "")).lower() == "inflation"
    ]
    if not inflation:
        return _skipped_overlay(
            "inflation_pm_overlay",
            reason="missing_required_inputs",
            inputs={"required": ["probability observations with macro_topic=inflation"]},
        )

    markets = _pm_market_rows(inflation)
    latest_as_of = max(obs.fetched_at for obs in inflation)
    return SignalResult(
        name="inflation_pm_overlay",
        status="computed",
        value=None,
        inputs={"markets": markets},
        metadata={},
        as_of=latest_as_of,
    )


def build_fed_rate_context(observations: list[NormalizedObservation]) -> SignalResult:
    by_key = _latest_by_series_key(observations)
    fed_obs = by_key.get("FEDFUNDS")
    fed_markets = [
        obs
        for obs in observations
        if obs.value_kind == "probability"
        and str(obs.metadata.get("macro_topic", "")).lower() == "fed"
    ]

    if fed_obs is None and not fed_markets:
        return _skipped_overlay(
            "fed_rate_context",
            reason="missing_required_inputs",
            inputs={"required": ["FEDFUNDS and/or Kalshi fed markets"]},
        )

    inputs: dict[str, Any] = {}
    as_of = datetime.now(timezone.utc)

    if fed_obs is not None:
        inputs["effective_rate"] = fed_obs.value
        inputs["unit"] = "percent"
        as_of = fed_obs.fetched_at

    if fed_markets:
        kalshi = _pm_market_rows(fed_markets)
        inputs["kalshi_markets"] = kalshi
        as_of = max(as_of, max(obs.fetched_at for obs in fed_markets))

    return SignalResult(
        name="fed_rate_context",
        status="computed",
        value=None,
        inputs=inputs,
        metadata={},
        as_of=as_of,
    )


def _pm_market_rows(observations: list[NormalizedObservation]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for obs in sorted(
        observations,
        key=lambda item: (
            item.metadata.get("strike") if item.metadata.get("strike") is not None else 0,
            item.series_key,
        ),
    ):
        row: dict[str, Any] = {
            "market_ticker": obs.series_key,
            "outcome_label": obs.metadata.get("outcome_label"),
            "yes_probability": obs.value,
            "event_ticker": obs.metadata.get("event_ticker"),
            "url": obs.metadata.get("url"),
        }
        strike = obs.metadata.get("strike")
        if strike is not None:
            row["strike"] = strike
        rows.append(row)
    return rows


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


def _skipped_overlay(
    name: str,
    *,
    reason: str,
    inputs: dict[str, object] | None = None,
) -> SignalResult:
    return SignalResult(
        name=name,
        status="skipped",
        value=None,
        reason=reason,
        inputs=inputs or {},
        as_of=datetime.now(timezone.utc),
    )
