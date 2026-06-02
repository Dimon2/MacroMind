from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_market_terminal.crawlers.base import BaseCrawler
from ai_market_terminal.db.repository import MacroRepository
from ai_market_terminal.market.market_watchlist import MarketTickerConfig, load_market_watchlist
from ai_market_terminal.market.yfinance_client import LatestBar, YFinanceClient
from ai_market_terminal.models import DataPoint


class MarketCrawler(BaseCrawler):
    name = "yfinance"

    def fetch(self, config: dict[str, Any]) -> list[DataPoint]:
        watchlist_path = config.get("watchlist_path")
        path = Path(watchlist_path) if watchlist_path else None
        watchlist = load_market_watchlist(path)

        print(f"[{self.name}] Fetch started: tickers={len(watchlist)}")

        client = YFinanceClient()
        datapoints: list[DataPoint] = []
        for ticker_config in watchlist:
            point = self._fetch_ticker(client, ticker_config)
            if point is not None:
                datapoints.append(point)
            time.sleep(0.2)

        print(f"[{self.name}] Fetch done: produced={len(datapoints)}")
        return datapoints

    def _fetch_ticker(
        self, client: YFinanceClient, ticker_config: MarketTickerConfig
    ) -> DataPoint | None:
        symbols = [ticker_config.symbol]
        if ticker_config.fallback_symbol:
            symbols.append(ticker_config.fallback_symbol)

        for symbol in symbols:
            try:
                bar = client.get_latest_bar(symbol)
            except Exception as exc:
                print(f"[{self.name}] Failed {symbol}: {exc}")
                bar = None

            if bar is not None:
                return self._bar_to_datapoint(ticker_config, bar, resolved_symbol=symbol)

            if symbol != symbols[-1]:
                print(f"[{self.name}] {symbol} unavailable, trying fallback")

        print(f"[{self.name}] No data for {ticker_config.indicator}")
        return None

    def _bar_to_datapoint(
        self,
        ticker_config: MarketTickerConfig,
        bar: LatestBar,
        *,
        resolved_symbol: str,
    ) -> DataPoint:
        now_utc = datetime.now(timezone.utc)
        metadata: dict[str, Any] = {
            "category": ticker_config.category,
            **bar.metadata,
        }
        if resolved_symbol != ticker_config.symbol:
            metadata["resolved_symbol"] = resolved_symbol
            metadata["requested_symbol"] = ticker_config.symbol

        return DataPoint(
            source=self.name,
            indicator=ticker_config.indicator,
            value=bar.close,
            unit=ticker_config.unit,
            period=bar.observation_date.isoformat(),
            fetched_at=now_utc,
            metadata=metadata,
        )

    def persist(self, config: dict[str, Any] | None = None) -> int:
        snapshots = self.fetch(config or {})
        repo = MacroRepository()
        count = repo.save_datapoints(snapshots)
        print(f"[{self.name}] Persisted observations: {count}")
        return count
