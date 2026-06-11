from __future__ import annotations

from datetime import date
from typing import Any

_cache: dict[date, dict[str, Any]] = {}


def get(query_date: date) -> dict[str, Any] | None:
    return _cache.get(query_date)


def set(query_date: date, response: dict[str, Any]) -> None:
    _cache[query_date] = response


def clear() -> None:
    _cache.clear()
