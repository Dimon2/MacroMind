from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from macromind.settings import get_settings


@dataclass(frozen=True)
class MarketTickerConfig:
    indicator: str
    symbol: str
    category: str
    unit: str
    fallback_symbol: str | None = None


def load_market_watchlist(path: Path | None = None) -> list[MarketTickerConfig]:
    settings = get_settings()
    watchlist_path = path or (settings.repo_root / "config" / "market_tickers.yaml")
    raw = yaml.safe_load(watchlist_path.read_text(encoding="utf-8"))
    entries: list[dict[str, Any]] = raw.get("tickers", [])
    configs: list[MarketTickerConfig] = []
    for entry in entries:
        configs.append(
            MarketTickerConfig(
                indicator=str(entry["indicator"]).upper(),
                symbol=str(entry["symbol"]),
                category=str(entry["category"]),
                unit=str(entry["unit"]),
                fallback_symbol=(
                    str(entry["fallback_symbol"]) if entry.get("fallback_symbol") else None
                ),
            )
        )
    return configs
