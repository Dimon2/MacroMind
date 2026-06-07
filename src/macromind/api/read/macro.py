from __future__ import annotations

from typing import Any, Literal

from macromind.db.repository import MacroRepository

from macromind.api.serializers import SCHEMA_VERSION, datapoint_to_observation_dict

MacroSource = Literal["fred", "yfinance"]

MACRO_SOURCES: tuple[str, ...] = ("fred", "yfinance")
MACRO_LIMIT_DEFAULT = 30
MACRO_LIMIT_MAX = 500


class SeriesNotFoundError(Exception):
    pass


def clamp_macro_limit(limit: int) -> int:
    return max(1, min(limit, MACRO_LIMIT_MAX))


def load_macro_series(
    series_id: str,
    *,
    source: MacroSource = "fred",
    limit: int = MACRO_LIMIT_DEFAULT,
    macro_repo: MacroRepository | None = None,
) -> dict[str, Any]:
    normalized_id = series_id.upper()
    effective_limit = clamp_macro_limit(limit)
    repo = macro_repo or MacroRepository()
    points = repo.load_observations(source, [normalized_id], last_n=effective_limit)
    if not points:
        raise SeriesNotFoundError()

    metadata = points[0].metadata or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "deterministic": True,
        "source": source,
        "series_id": normalized_id,
        "title": metadata.get("title"),
        "units": points[0].unit or None,
        "frequency": metadata.get("frequency"),
        "category": metadata.get("category"),
        "limit": effective_limit,
        "count": len(points),
        "observations": [datapoint_to_observation_dict(dp) for dp in points],
    }
