from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from macromind.db.signal_snapshot import SignalSnapshotRepository, SignalSnapshotRow
from macromind.ingestion.crawl_status import build_crawl_status
from macromind.signals.calculators import MARKET_STATE_DIMENSIONS
from macromind.signals.delta import SignalDelta, build_deltas

PERSIST_CRAWLERS = ("fred", "kalshi", "market")


@dataclass(frozen=True)
class BriefContext:
    snapshot_date: date
    previous_snapshot_date: date | None
    as_of: datetime
    snapshots_by_name: dict[str, SignalSnapshotRow]
    deltas: list[SignalDelta]
    crawl_status: dict[str, Any]

    def snapshot(self, signal_name: str) -> SignalSnapshotRow | None:
        return self.snapshots_by_name.get(signal_name)

    def dimension_labels(self) -> dict[str, str | None]:
        return {
            name: (row.label if row and row.status == "computed" else None)
            for name, row in (
                (name, self.snapshots_by_name.get(name)) for name in MARKET_STATE_DIMENSIONS
            )
        }


def load_brief_context(
    snapshot_date: date,
    *,
    snapshot_repo: SignalSnapshotRepository | None = None,
    crawler_names: tuple[str, ...] = PERSIST_CRAWLERS,
) -> BriefContext | None:
    repo = snapshot_repo or SignalSnapshotRepository()
    rows = repo.load_for_date(snapshot_date)
    if not rows:
        return None

    prev_date, deltas = build_deltas(rows, repo)
    as_of = max(row.as_of for row in rows)
    crawl_status = build_crawl_status(crawler_names)

    return BriefContext(
        snapshot_date=snapshot_date,
        previous_snapshot_date=prev_date,
        as_of=as_of,
        snapshots_by_name={row.signal_name: row for row in rows},
        deltas=deltas,
        crawl_status=crawl_status,
    )
