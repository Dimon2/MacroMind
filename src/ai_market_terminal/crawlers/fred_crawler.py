from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from ai_market_terminal.crawlers.base import BaseCrawler
from ai_market_terminal.db.repository import MacroRepository
from ai_market_terminal.macro.fred_client import FredClient
from ai_market_terminal.macro.fred_watchlist import FredSeriesConfig, load_fred_watchlist
from ai_market_terminal.models import DataPoint


class FredCrawler(BaseCrawler):
    name = "fred"

    def fetch(self, config: dict[str, Any]) -> list[DataPoint]:
        watchlist_path = config.get("watchlist_path")
        path = Path(watchlist_path) if watchlist_path else None
        watchlist = load_fred_watchlist(path)

        print(f"[{self.name}] Fetch started: series={len(watchlist)}")

        datapoints: list[DataPoint] = []
        with FredClient() as client:
            for series_config in watchlist:
                point = self._fetch_series(client, series_config)
                if point is not None:
                    datapoints.append(point)
                time.sleep(0.2)

        print(f"[{self.name}] Fetch done: produced={len(datapoints)}")
        return datapoints

    def _fetch_series(
        self, client: FredClient, series_config: FredSeriesConfig
    ) -> DataPoint | None:
        series_ids = [series_config.series_id]
        if series_config.fallback_series_id:
            series_ids.append(series_config.fallback_series_id)

        for series_id in series_ids:
            try:
                return self._fetch_one(client, series_config, series_id)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (400, 404) and series_id != series_ids[-1]:
                    print(
                        f"[{self.name}] {series_id} unavailable ({exc.response.status_code}), "
                        f"trying fallback"
                    )
                    continue
                print(f"[{self.name}] Failed {series_id}: {exc}")
                return None
            except Exception as exc:
                print(f"[{self.name}] Failed {series_id}: {exc}")
                return None
        return None

    def _fetch_one(
        self,
        client: FredClient,
        series_config: FredSeriesConfig,
        series_id: str,
    ) -> DataPoint | None:
        info = client.get_series_info(series_id)
        latest = client.get_latest_observation(series_id)
        if latest is None:
            print(f"[{self.name}] No observations for {series_id}")
            return None

        obs_date, value = latest
        now_utc = datetime.now(timezone.utc)
        unit = (
            info.get("units_short")
            or info.get("units")
            or series_config.unit
        )

        metadata: dict[str, Any] = {
            "category": series_config.category,
            "title": info.get("title"),
            "frequency": info.get("frequency"),
            "frequency_short": info.get("frequency_short"),
            "seasonal_adjustment": info.get("seasonal_adjustment"),
        }
        if series_id != series_config.series_id:
            metadata["resolved_series_id"] = series_id
            metadata["requested_series_id"] = series_config.series_id

        return DataPoint(
            source=self.name,
            indicator=series_id,
            value=value,
            unit=str(unit),
            period=obs_date.isoformat(),
            fetched_at=now_utc,
            metadata=metadata,
        )

    def persist(self, config: dict[str, Any] | None = None) -> int:
        snapshots = self.fetch(config or {})
        repo = MacroRepository()
        count = repo.save_datapoints(snapshots)
        print(f"[{self.name}] Persisted observations: {count}")
        return count
