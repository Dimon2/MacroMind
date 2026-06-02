from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal

ValueKind = Literal["level", "probability", "rate", "spread"]


@dataclass(frozen=True)
class NormalizedObservation:
    source: str
    series_key: str
    observation_date: date
    fetched_at: datetime
    value_kind: ValueKind
    value: float
    unit: str
    metadata: dict[str, Any] = field(default_factory=dict)
