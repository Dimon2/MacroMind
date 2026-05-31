from __future__ import annotations

import time
from typing import Any

import httpx

from ai_market_terminal.settings import get_settings


class KalshiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.kalshi_api_base).rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={"User-Agent": "AI-Market-Terminal/0.1"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> KalshiClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(4):
            response = self._client.request(method, path, **kwargs)
            if response.status_code != 429:
                response.raise_for_status()
                return response
            last_error = httpx.HTTPStatusError(
                "429 Too Many Requests",
                request=response.request,
                response=response,
            )
            time.sleep(0.5 * (2**attempt))
        if last_error:
            raise last_error
        raise RuntimeError("Kalshi request failed")

    def list_markets(self, *, series_ticker: str, limit: int = 200) -> list[dict[str, Any]]:
        params = {
            "limit": limit,
            "status": "open",
            "series_ticker": series_ticker.upper(),
        }
        response = self._request("GET", "/markets", params=params)
        payload = response.json()
        return payload.get("markets", [])
