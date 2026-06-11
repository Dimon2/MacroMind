from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from macromind.api.read.desk import NoSnapshotsError, load_latest_desk
from macromind.api.read.health import build_health_response
from macromind.api.read.macro import (
    MACRO_LIMIT_DEFAULT,
    SeriesNotFoundError,
    load_macro_series,
)
from macromind.api.read.regime_lab import (
    FredApiKeyMissingError,
    InvalidQueryDateError,
    compute_regime_lab,
    get_episodes,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="MacroMind API",
        description=(
            "Read-only API: /desk and /macro use persisted DB; "
            "/lab/regime replays historical point-in-time regime computation."
        ),
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
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

    @app.get("/lab/regime/episodes")
    def lab_regime_episodes() -> dict:
        return get_episodes()

    @app.get("/lab/regime/compute")
    def lab_regime_compute(
        query_date: str = Query(..., alias="date", description="ISO date YYYY-MM-DD"),
    ) -> dict:
        try:
            as_of = date.fromisoformat(query_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid date format; use YYYY-MM-DD") from exc
        try:
            return compute_regime_lab(as_of)
        except InvalidQueryDateError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FredApiKeyMissingError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return app
