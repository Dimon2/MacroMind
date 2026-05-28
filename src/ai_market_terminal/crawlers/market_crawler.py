from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ai_market_terminal.crawlers.base import BaseCrawler
from ai_market_terminal.models import DataPoint


class MarketCrawler(BaseCrawler):
    name = "yfinance"

    DEFAULT_TICKERS = {
        "VIX": "^VIX",
        "DXY": "DX-Y.NYB",
        "GOLD": "GC=F",
        "WTI_OIL": "CL=F",
    }

    def fetch(self, config: dict[str, Any]) -> list[DataPoint]:
        tickers = config.get("tickers", self.DEFAULT_TICKERS)
        now_utc = datetime.now(timezone.utc)
        period = now_utc.strftime("%Y-%m-%dT%H:00:00Z")

        print(f"[{self.name}] Fetch started: tickers={len(tickers)}")

        datapoints: list[DataPoint] = []
        for indicator, ticker in tickers.items():
            datapoints.append(
                DataPoint(
                    source=self.name,
                    indicator=indicator,
                    value=0.0,  # TODO: Replace with real market price.
                    unit="index",
                    period=period,
                    fetched_at=now_utc,
                    metadata={"ticker": ticker, "stub": True},
                )
            )

        print(f"[{self.name}] Fetch done: produced={len(datapoints)}")
        return datapoints

