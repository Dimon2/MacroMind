from __future__ import annotations

from datetime import date

from macromind.brief.context import load_brief_context
from macromind.brief.renderer import render_brief
from macromind.db.signal_snapshot import SignalSnapshotRepository
from macromind.signals.pipeline import utc_today


class NoSnapshotError(Exception):
    def __init__(self, snapshot_date: date) -> None:
        self.snapshot_date = snapshot_date
        super().__init__(f"No snapshots for {snapshot_date.isoformat()}")


def run_brief(
    *,
    snapshot_repo: SignalSnapshotRepository | None = None,
) -> str:
    day = utc_today()
    ctx = load_brief_context(day, snapshot_repo=snapshot_repo)
    if ctx is None:
        raise NoSnapshotError(day)
    return render_brief(ctx)
