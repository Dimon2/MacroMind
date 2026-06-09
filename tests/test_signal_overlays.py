from __future__ import annotations

from datetime import date, datetime, timezone

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.overlays import build_fed_rate_context, build_inflation_pm_overlay

_FETCHED = datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc)


def test_build_inflation_pm_overlay_lists_markets() -> None:
    observations = [
        NormalizedObservation(
            source="kalshi",
            series_key="KXCPI-1",
            observation_date=date(2026, 6, 1),
            fetched_at=_FETCHED,
            value_kind="probability",
            value=0.4,
            unit="probability",
            metadata={"macro_topic": "inflation", "outcome_label": "Above 3%", "strike": 3.0},
        ),
        NormalizedObservation(
            source="kalshi",
            series_key="KXCPI-2",
            observation_date=date(2026, 6, 1),
            fetched_at=_FETCHED,
            value_kind="probability",
            value=0.12,
            unit="probability",
            metadata={"macro_topic": "inflation", "outcome_label": "Above 4%", "strike": 4.0},
        ),
    ]
    result = build_inflation_pm_overlay(observations)
    assert result.status == "computed"
    assert result.value is None
    markets = result.inputs["markets"]
    assert len(markets) == 2
    assert markets[0]["yes_probability"] == 0.4


def test_build_fed_rate_context_effective_and_kalshi() -> None:
    observations = [
        NormalizedObservation(
            source="fred",
            series_key="FEDFUNDS",
            observation_date=date(2026, 5, 1),
            fetched_at=_FETCHED,
            value_kind="rate",
            value=4.25,
            unit="percent",
            metadata={},
        ),
        NormalizedObservation(
            source="kalshi",
            series_key="KXFED-CUT",
            observation_date=date(2026, 6, 1),
            fetched_at=_FETCHED,
            value_kind="probability",
            value=0.68,
            unit="probability",
            metadata={"macro_topic": "fed", "outcome_label": "Cut 25bp by Sep"},
        ),
    ]
    result = build_fed_rate_context(observations)
    assert result.status == "computed"
    assert result.inputs["effective_rate"] == 4.25
    assert len(result.inputs["kalshi_markets"]) == 1
