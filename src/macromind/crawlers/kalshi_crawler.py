from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any

from ai_market_terminal.crawlers.base import BaseCrawler
from ai_market_terminal.db.repository import PredictionMarketRepository
from ai_market_terminal.models import DataPoint
from ai_market_terminal.prediction_markets.kalshi_client import KalshiClient
from ai_market_terminal.prediction_markets.models import PredictionMarketSnapshot
from ai_market_terminal.prediction_markets.resolver import EventMarketResolver
from ai_market_terminal.prediction_markets.watchlist import load_watchlist


class KalshiCrawler(BaseCrawler):
    name = "kalshi"

    def fetch(self, config: dict[str, Any]) -> list[DataPoint]:
        return [self._snapshot_to_datapoint(s) for s in self.fetch_snapshots(config)]

    @staticmethod
    def _snapshot_to_datapoint(snapshot: PredictionMarketSnapshot) -> DataPoint:
        meta = asdict(snapshot)
        meta.pop("yes_probability", None)
        meta.pop("period_date", None)
        meta.pop("fetched_at", None)
        meta.pop("platform", None)
        meta.pop("market_ticker", None)
        if meta.get("event_close_at") is not None:
            meta["event_close_at"] = snapshot.event_close_at.isoformat()
        return DataPoint(
            source=snapshot.platform,
            indicator=snapshot.market_ticker,
            value=snapshot.yes_probability,
            unit=snapshot.unit_hint or "probability",
            period=snapshot.period_date.isoformat(),
            fetched_at=snapshot.fetched_at,
            metadata=meta,
        )

    def fetch_snapshots(
        self, config: dict[str, Any] | None = None
    ) -> list[PredictionMarketSnapshot]:
        cfg = config or {}
        watchlist_path = cfg.get("watchlist_path")
        watchlist = load_watchlist(watchlist_path) if watchlist_path else load_watchlist()

        snapshots: list[PredictionMarketSnapshot] = []
        print(f"[{self.name}] Fetch started: series={len(watchlist)}")

        with KalshiClient() as client:
            resolver = EventMarketResolver(client)
            for series_config in watchlist:
                try:
                    snapshots.extend(resolver.resolve_series(series_config))
                except Exception as exc:
                    print(
                        f"[{self.name}] Failed series {series_config.series_ticker}: {exc}"
                    )
                time.sleep(0.3)

        print(f"[{self.name}] Fetch done: snapshots={len(snapshots)}")
        print(f"[{self.name}] snapshots by series: { {s.series_ticker for s in snapshots} }")
        return snapshots

    def persist(self, config: dict[str, Any] | None = None) -> int:
        snapshots = self.fetch_snapshots(config)
        repo = PredictionMarketRepository()
        count = repo.save_snapshots(snapshots)
        print(f"[{self.name}] Persisted observations: {count}")
        return count
