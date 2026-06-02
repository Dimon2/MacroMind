from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macromind.crawlers.base import BaseCrawler
from macromind.models import DataPoint


class PolymarketCrawler(BaseCrawler):
    name = "polymarket"

    DEFAULT_MARKETS = [
        "fed_rate_decision",
        "us_recession_probability",
    ]

    def fetch(self, config: dict[str, Any]) -> list[DataPoint]:
        markets = config.get("markets", self.DEFAULT_MARKETS)
        now_utc = datetime.now(timezone.utc)
        period = now_utc.strftime("%Y-%m-%d")

        print(f"[{self.name}] Fetch started: markets={len(markets)}")

        datapoints = [
            DataPoint(
                source=self.name,
                indicator=market,
                value=0.0,  # TODO: Replace with real implied probability.
                unit="probability",
                period=period,
                fetched_at=now_utc,
                metadata={"stub": True},
            )
            for market in markets
        ]

        print(f"[{self.name}] Fetch done: produced={len(datapoints)}")
        return datapoints

