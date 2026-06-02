from __future__ import annotations

from typing import Any

from macromind.crawlers import (
    FredCrawler,
    KalshiCrawler,
    MarketCrawler,
    NyFedCrawler,
    PolymarketCrawler,
)
from macromind.models import DataPoint


class CrawlerRunner:
    def __init__(self) -> None:
        self._registry = {
            "fred": FredCrawler(),
            "market": MarketCrawler(),
            "nyfed": NyFedCrawler(),
            "polymarket": PolymarketCrawler(),
            "kalshi": KalshiCrawler(),
        }

    def list_crawlers(self) -> list[str]:
        return sorted(self._registry.keys())

    def run_one(self, crawler_name: str, config: dict[str, Any] | None = None) -> list[DataPoint]:
        if crawler_name not in self._registry:
            raise ValueError(f"Unknown crawler: {crawler_name}")

        cfg = config or {}
        crawler = self._registry[crawler_name]
        print(f"[runner] Running crawler: {crawler_name}")
        datapoints = crawler.fetch(cfg)
        print(f"[runner] Done crawler: {crawler_name}, datapoints={len(datapoints)}")
        return datapoints

    def run_all(self, configs: dict[str, dict[str, Any]] | None = None) -> dict[str, list[DataPoint]]:
        cfgs = configs or {}
        result: dict[str, list[DataPoint]] = {}
        for crawler_name in self.list_crawlers():
            result[crawler_name] = self.run_one(crawler_name, cfgs.get(crawler_name, {}))
        return result

    def persist_kalshi(self, config: dict[str, Any] | None = None) -> int:
        crawler = self._registry["kalshi"]
        return crawler.persist(config)

    def persist_fred(self, config: dict[str, Any] | None = None) -> int:
        crawler = self._registry["fred"]
        return crawler.persist(config)

    def persist_market(self, config: dict[str, Any] | None = None) -> int:
        crawler = self._registry["market"]
        return crawler.persist(config)

