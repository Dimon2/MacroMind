from __future__ import annotations

from typing import Any

from macromind.db.signal_snapshot import SignalSnapshotRepository
from macromind.signals.delta import build_deltas_for_date

from macromind.api.serializers import SCHEMA_VERSION, snapshot_row_to_signal_dict


class NoSnapshotsError(Exception):
    pass


def load_latest_signals(
    *,
    snapshot_repo: SignalSnapshotRepository | None = None,
) -> dict[str, Any]:
    repo = snapshot_repo or SignalSnapshotRepository()
    latest_date = repo.load_latest_date()
    if latest_date is None:
        raise NoSnapshotsError()

    rows = repo.load_for_date(latest_date)
    if not rows:
        raise NoSnapshotsError()

    prev_date, deltas = build_deltas_for_date(latest_date, repo)
    coverage = {
        "computed": sum(1 for row in rows if row.status == "computed"),
        "skipped": sum(1 for row in rows if row.status == "skipped"),
        "total": len(rows),
    }
    as_of = max(row.as_of for row in rows).isoformat()

    return {
        "schema_version": SCHEMA_VERSION,
        "deterministic": True,
        "snapshot_date": latest_date.isoformat(),
        "as_of": as_of,
        "coverage": coverage,
        "signals": [snapshot_row_to_signal_dict(row) for row in rows],
        "deltas": [delta.to_dict() for delta in deltas],
        "previous_snapshot_date": prev_date.isoformat() if prev_date else None,
    }
