from __future__ import annotations

import time
from datetime import date
from typing import Any

import httpx

from ai_market_terminal.settings import get_settings

FRED_API_BASE = "https://api.stlouisfed.org/fred"
# FRED JSON plural for /series and /series/search — documented key, not a typo.
FRED_SERIES_LIST_KEY = "seriess"


def parse_latest_observation(
    observations: list[dict[str, Any]],
) -> tuple[date, float] | None:
    for obs in observations:
        raw_value = obs.get("value")
        if raw_value is None or raw_value == ".":
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        raw_date = obs.get("date")
        if not raw_date:
            continue
        try:
            obs_date = date.fromisoformat(str(raw_date))
        except ValueError:
            continue
        return obs_date, value
    return None


class FredClient:
    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        settings = get_settings()
        key = api_key if api_key is not None else settings.fred_api_key
        if not key:
            raise ValueError(
                "FRED_API_KEY is not set. Add it to .env or pass api_key to FredClient."
            )
        self._api_key = key
        self._client = httpx.Client(
            base_url=FRED_API_BASE,
            timeout=timeout,
            headers={"User-Agent": "AI-Market-Terminal/0.1"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> FredClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = {"api_key": self._api_key, "file_type": "json", **(params or {})}
        last_error: Exception | None = None
        for attempt in range(4):
            response = self._client.get(path, params=query)
            if response.status_code != 429:
                response.raise_for_status()
                return response.json()
            last_error = httpx.HTTPStatusError(
                "429 Too Many Requests",
                request=response.request,
                response=response,
            )
            time.sleep(0.5 * (2**attempt))
        if last_error:
            raise last_error
        raise RuntimeError("FRED request failed")

    def get_series_info(self, series_id: str) -> dict[str, Any]:
        payload = self._request("/series", {"series_id": series_id})
        series_list = payload.get(FRED_SERIES_LIST_KEY) or []
        if not series_list:
            return {}
        return series_list[0]

    def get_observations(
        self, series_id: str, *, limit: int = 10, sort_order: str = "desc"
    ) -> list[dict[str, Any]]:
        payload = self._request(
            "/series/observations",
            {
                "series_id": series_id,
                "sort_order": sort_order,
                "limit": limit,
            },
        )
        return payload.get("observations", [])

    def get_latest_observation(
        self, series_id: str, *, limit: int = 10
    ) -> tuple[date, float] | None:
        observations = self.get_observations(series_id, limit=limit)
        return parse_latest_observation(observations)
