from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ai_market_terminal.settings import get_settings


@dataclass(frozen=True)
class FredSeriesConfig:
    series_id: str
    category: str
    unit: str
    fallback_series_id: str | None = None


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
            )
        )
    return configs
