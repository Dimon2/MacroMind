from __future__ import annotations

from datetime import date
from typing import Any

from macromind.market.normalized_observation import NormalizedObservation, ValueKind
from macromind.models import DataPoint
from macromind.prediction_markets.models import PredictionMarketSnapshot


def normalize_macro_datapoint(datapoint: DataPoint) -> NormalizedObservation:
    metadata = dict(datapoint.metadata or {})
    metadata.setdefault("indicator", datapoint.indicator)
    return NormalizedObservation(
        source=datapoint.source,
        series_key=datapoint.indicator,
        observation_date=date.fromisoformat(datapoint.period),
        fetched_at=datapoint.fetched_at,
        value_kind=_macro_value_kind(datapoint.unit, metadata),
        value=datapoint.value,
        unit=datapoint.unit,
        metadata=metadata,
    )


def normalize_prediction_snapshot(snapshot: PredictionMarketSnapshot) -> NormalizedObservation:
    metadata: dict[str, Any] = {
        "series_ticker": snapshot.series_ticker,
        "macro_topic": snapshot.macro_topic,
        "event_ticker": snapshot.event_ticker,
        "outcome_type": snapshot.outcome_type,
        "outcome_label": snapshot.outcome_label,
        "outcome_key": snapshot.outcome_key,
        "strike": snapshot.strike,
        "strike_op": snapshot.strike_op,
        "unit_hint": snapshot.unit_hint,
        "series_slug": snapshot.series_slug,
        "series_title": snapshot.series_title,
        "event_title": snapshot.event_title,
        "reference_period": snapshot.reference_period,
        "event_close_at": (
            snapshot.event_close_at.isoformat() if snapshot.event_close_at is not None else None
        ),
        "yes_bid": snapshot.yes_bid,
        "yes_ask": snapshot.yes_ask,
        "volume": snapshot.volume,
        "url": snapshot.url,
        **snapshot.metadata,
    }
    return NormalizedObservation(
        source=snapshot.platform,
        series_key=snapshot.market_ticker,
        observation_date=snapshot.period_date,
        fetched_at=snapshot.fetched_at,
        value_kind="probability",
        value=snapshot.yes_probability,
        unit=snapshot.unit_hint or "probability",
        metadata=metadata,
    )


def _macro_value_kind(unit: str, metadata: dict[str, Any]) -> ValueKind:
    lowered = unit.lower()
    if "%" in lowered or "percent" in lowered or "pct" in lowered:
        return "rate"

    frequency = str(metadata.get("frequency", "")).lower()
    if "percent" in frequency:
        return "rate"

    return "level"
