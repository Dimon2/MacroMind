from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

SignalStatus = Literal["computed", "skipped"]


@dataclass(frozen=True)
class SignalResult:
    name: str
    status: SignalStatus
    value: float | None = None
    reason: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    as_of: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "value": self.value,
            "reason": self.reason,
            "inputs": self.inputs,
            "metadata": self.metadata,
            "as_of": self.as_of.isoformat(),
        }
