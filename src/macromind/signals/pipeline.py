from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from macromind.db.repository import MacroRepository, PredictionMarketRepository
from macromind.db.signal_snapshot import SignalSnapshotRepository
from macromind.market.normalized_feed_service import NormalizedFeedService
from macromind.signals.delta import build_deltas_for_date
from macromind.signals.service import SignalService


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def load_observations_and_compute(
    *,
    macro_repo: MacroRepository | None = None,
    pm_repo: PredictionMarketRepository | None = None,
    signal_service: SignalService | None = None,
) -> dict[str, Any]:
    macro = macro_repo or MacroRepository()
    pm = pm_repo or PredictionMarketRepository()
    service = signal_service or SignalService()
    feed = NormalizedFeedService()
    normalized = feed.combine(
        macro_datapoints=macro.load_latest_datapoints(),
        prediction_snapshots=pm.load_latest_snapshots(),
    )
    return service.compute(normalized)


def run_snapshot_signals(
    snapshot_date: date | None = None,
    *,
    snapshot_repo: SignalSnapshotRepository | None = None,
    macro_repo: MacroRepository | None = None,
    pm_repo: PredictionMarketRepository | None = None,
    signal_service: SignalService | None = None,
) -> dict[str, Any]:
    repo = snapshot_repo or SignalSnapshotRepository()
    day = snapshot_date or utc_today()

    macro = macro_repo or MacroRepository()
    pm = pm_repo or PredictionMarketRepository()
    service = signal_service or SignalService()
    feed = NormalizedFeedService()
    normalized = feed.combine(
        macro_datapoints=macro.load_latest_datapoints(),
        prediction_snapshots=pm.load_latest_snapshots(),
    )
    results = service.compute_results(normalized)
    saved = repo.upsert_for_date(day, results)
    prev_date, deltas = build_deltas_for_date(day, repo)

    coverage = {
        "computed": sum(1 for r in results if r.status == "computed"),
        "skipped": sum(1 for r in results if r.status == "skipped"),
        "total": len(results),
    }
    as_of = (
        max((r.as_of for r in results), default=datetime.now(timezone.utc)).isoformat()
    )

    return {
        "snapshot_date": day.isoformat(),
        "saved": saved,
        "as_of": as_of,
        "coverage": coverage,
        "signals": [r.to_dict() for r in results],
        "deltas": [delta.to_dict() for delta in deltas],
        "previous_snapshot_date": prev_date.isoformat() if prev_date else None,
    }
