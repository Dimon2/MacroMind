from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal


Platform = Literal["kalshi", "polymarket"]
OutcomeType = Literal["threshold", "categorical"]
MacroTopic = Literal["fed", "inflation", "employment", "gdp", "commodities"]


@dataclass
class PredictionMarketSnapshot:
    platform: Platform
    series_ticker: str
    macro_topic: str
    event_ticker: str
    market_ticker: str
    outcome_type: OutcomeType
    outcome_label: str
    yes_probability: float
    period_date: date
    fetched_at: datetime
    outcome_key: str | None = None
    strike: float | None = None
    strike_op: str | None = None
    unit_hint: str | None = None
    series_slug: str | None = None
    series_title: str | None = None
    event_title: str | None = None
    reference_period: str | None = None
    event_close_at: datetime | None = None
    yes_bid: float | None = None
    yes_ask: float | None = None
    volume: float | None = None
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
