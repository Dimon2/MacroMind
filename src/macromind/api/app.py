from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException, Query

from macromind.api.read.desk import NoSnapshotsError, load_latest_desk
from macromind.api.read.health import build_health_response
from macromind.api.read.macro import (
    MACRO_LIMIT_DEFAULT,
    SeriesNotFoundError,
    load_macro_series,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="MacroMind API",
        description="Read-only API over persisted macro data and signal snapshots.",
        version="0.1.0",
    )

    @app.get("/health")
    def health(
        freshness: bool = Query(default=False, description="Include crawl_runs freshness"),
    ) -> dict:
        return build_health_response(include_freshness=freshness)

    @app.get("/desk/latest")
    def desk_latest() -> dict:
        try:
            return load_latest_desk()
        except NoSnapshotsError:
            raise HTTPException(status_code=404, detail="no signal snapshots found")

    @app.get("/macro/{series_id}")
    def macro_series(
        series_id: str,
        limit: int = Query(default=MACRO_LIMIT_DEFAULT, ge=1),
        source: Literal["fred", "yfinance"] = Query(default="fred"),
    ) -> dict:
        try:
            return load_macro_series(series_id, source=source, limit=limit)
        except SeriesNotFoundError:
            raise HTTPException(
                status_code=404,
                detail="series not found or no observations",
            )

    return app
