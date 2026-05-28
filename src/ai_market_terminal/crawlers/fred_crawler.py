from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ai_market_terminal.crawlers.base import BaseCrawler
from ai_market_terminal.models import DataPoint


class FredCrawler(BaseCrawler):
    name = "fred"

    DEFAULT_INDICATORS = [
        "DGS10",
        "DGS2",
        "T10Y2Y",
        "FEDFUNDS",
        "CPIAUCSL",
        "WALCL",
        "M2SL",
        "WRESBAL",
        "BAMLH0A0HYM2",
    ]

    def fetch(self, config: dict[str, Any]) -> list[DataPoint]:
        indicators = config.get("indicators", self.DEFAULT_INDICATORS)
        now_utc = datetime.now(timezone.utc)
        period = now_utc.strftime("%Y-%m-%d")

        print(f"[{self.name}] Fetch started: indicators={len(indicators)}")

        datapoints = [
            DataPoint(
                source=self.name,
                indicator=indicator,
                value=0.0,  # TODO: Replace with real FRED value.
                unit=config.get("unit_overrides", {}).get(indicator, "index"),
                period=period,
                fetched_at=now_utc,
                metadata={"stub": True},
            )
            for indicator in indicators
        ]

        print(f"[{self.name}] Fetch done: produced={len(datapoints)}")
        return datapoints

