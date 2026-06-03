from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from macromind.settings import get_settings


DEFAULT_MIN_POINTS = 1
DEFAULT_BOOTSTRAP_LIMIT = 15
DEFAULT_STEADY_LIMIT = 5


@dataclass(frozen=True)
class FredSeriesConfig:
    series_id: str
    category: str
    unit: str
    fallback_series_id: str | None = None
    min_points: int = DEFAULT_MIN_POINTS
    bootstrap_limit: int = DEFAULT_BOOTSTRAP_LIMIT
    steady_limit: int = DEFAULT_STEADY_LIMIT

    def fetch_limit_for_count(self, observation_count: int) -> int:
        if observation_count < self.min_points:
            return self.bootstrap_limit
        return self.steady_limit


def load_fred_watchlist(path: Path | None = None) -> list[FredSeriesConfig]:
    settings = get_settings()
    watchlist_path = path or (settings.repo_root / "config" / "fred_series.yaml")
    raw = yaml.safe_load(watchlist_path.read_text(encoding="utf-8"))
    entries: list[dict[str, Any]] = raw.get("series", [])
    configs: list[FredSeriesConfig] = []
    for entry in entries:
        configs.append(
            FredSeriesConfig(
                series_id=str(entry["series_id"]).upper(),
                category=str(entry["category"]),
                unit=str(entry["unit"]),
                fallback_series_id=(
                    str(entry["fallback_series_id"]).upper()
                    if entry.get("fallback_series_id")
                    else None
                ),
                min_points=int(entry.get("min_points", DEFAULT_MIN_POINTS)),
                bootstrap_limit=int(entry.get("bootstrap_limit", DEFAULT_BOOTSTRAP_LIMIT)),
                steady_limit=int(entry.get("steady_limit", DEFAULT_STEADY_LIMIT)),
            )
        )
    return configs
