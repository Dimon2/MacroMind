from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from macromind.db.signal_snapshot import SignalSnapshotRepository, SignalSnapshotRow


@dataclass(frozen=True)
class SignalDelta:
    signal_name: str
    status: str
    value: float | None
    label: str | None
    prev_value: float | None
    prev_label: str | None
    value_delta: float | None
    label_changed: bool
    comparable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_name": self.signal_name,
            "status": self.status,
            "value": self.value,
            "label": self.label,
            "prev_value": self.prev_value,
            "prev_label": self.prev_label,
            "value_delta": self.value_delta,
            "label_changed": self.label_changed,
            "comparable": self.comparable,
        }


def compute_signal_deltas(
    current: list[SignalSnapshotRow],
    previous: list[SignalSnapshotRow],
) -> list[SignalDelta]:
    prev_by_name = {row.signal_name: row for row in previous}
    deltas: list[SignalDelta] = []

    for row in current:
        prev = prev_by_name.get(row.signal_name)
        if prev is None:
            deltas.append(
                SignalDelta(
                    signal_name=row.signal_name,
                    status=row.status,
                    value=row.value,
                    label=row.label,
                    prev_value=None,
                    prev_label=None,
                    value_delta=None,
                    label_changed=False,
                    comparable=False,
                )
            )
            continue

        comparable = row.status == "computed" and prev.status == "computed"
        value_delta: float | None = None
        if comparable and row.value is not None and prev.value is not None:
            value_delta = row.value - prev.value

        deltas.append(
            SignalDelta(
                signal_name=row.signal_name,
                status=row.status,
                value=row.value,
                label=row.label,
                prev_value=prev.value,
                prev_label=prev.label,
                value_delta=value_delta,
                label_changed=row.label != prev.label,
                comparable=comparable,
            )
        )

    return deltas


def build_deltas(
    current: list[SignalSnapshotRow],
    repo: SignalSnapshotRepository | None = None,
) -> tuple[date | None, list[SignalDelta]]:
    if not current:
        return None, []

    snapshot_repo = repo or SignalSnapshotRepository()
    snapshot_date = current[0].snapshot_date
    prev_date = snapshot_repo.load_previous_date(snapshot_date)
    if prev_date is None:
        return None, compute_signal_deltas(current, [])

    previous = snapshot_repo.load_for_date(prev_date)
    return prev_date, compute_signal_deltas(current, previous)


def build_deltas_for_date(
    snapshot_date: date,
    repo: SignalSnapshotRepository | None = None,
) -> tuple[date | None, list[SignalDelta]]:
    snapshot_repo = repo or SignalSnapshotRepository()
    return build_deltas(snapshot_repo.load_for_date(snapshot_date), snapshot_repo)
