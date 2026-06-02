from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macromind.crawlers.base import BaseCrawler
from macromind.models import DataPoint


class NyFedCrawler(BaseCrawler):
    name = "nyfed"

    def fetch(self, config: dict[str, Any]) -> list[DataPoint]:
        indicator = config.get("indicator", "RRP")
        now_utc = datetime.now(timezone.utc)
        period = now_utc.strftime("%Y-%m-%d")

        print(f"[{self.name}] Fetch started: indicator={indicator}")

        datapoints = [
            DataPoint(
                source=self.name,
                indicator=indicator,
                value=0.0,  # TODO: Replace with real RRP balance.
                unit="USD_bln",
                period=period,
                fetched_at=now_utc,
                metadata={"stub": True},
            )
        ]

        print(f"[{self.name}] Fetch done: produced={len(datapoints)}")
        return datapoints

