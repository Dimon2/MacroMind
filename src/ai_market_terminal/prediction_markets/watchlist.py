from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ai_market_terminal.settings import get_settings


@dataclass(frozen=True)
class SeriesWatchConfig:
    series_ticker: str
    macro_topic: str
    slug: str | None = None
    market_mode: str = "rules"
    pick: str = "atm"
    max_markets: int = 2


def load_watchlist(path: Path | None = None) -> list[SeriesWatchConfig]:
    settings = get_settings()
    watchlist_path = path or (settings.repo_root / "config" / "kalshi_watchlist.yaml")
    raw = yaml.safe_load(watchlist_path.read_text(encoding="utf-8"))
    entries: list[dict[str, Any]] = raw.get("series", [])
    configs: list[SeriesWatchConfig] = []
    for entry in entries:
        markets = entry.get("markets") or {}
        configs.append(
            SeriesWatchConfig(
                series_ticker=str(entry["series_ticker"]).upper(),
                macro_topic=str(entry["macro_topic"]),
                slug=entry.get("slug"),
                market_mode=str(markets.get("mode", "rules")),
                pick=str(markets.get("pick", "atm")),
                max_markets=int(markets.get("max", 2)),
            )
        )
    return configs
