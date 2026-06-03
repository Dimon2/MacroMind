from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from psycopg.types.json import Json

from macromind.db.connection import connection_scope
from macromind.signals.models import SignalResult


@dataclass(frozen=True)
class SignalSnapshotRow:
    snapshot_date: date
    signal_name: str
    status: str
    value: float | None
    label: str | None
    reason: str | None
    inputs: dict
    metadata: dict
    as_of: datetime


def extract_label(result: SignalResult) -> str | None:
    if result.status != "computed":
        return None
    metadata = result.metadata or {}
    label = metadata.get("label")
    if label is not None:
        return str(label)
    curve_state = metadata.get("curve_state")
    if curve_state is not None:
        return str(curve_state)
    return None


class SignalSnapshotRepository:
    def upsert_for_date(self, snapshot_date: date, results: list[SignalResult]) -> int:
        if not results:
            return 0

        saved = 0
        with connection_scope() as conn:
            for result in results:
                conn.execute(
                    """
                    INSERT INTO signal_snapshots (
                      snapshot_date, signal_name, status, value, label, reason,
                      inputs, metadata, as_of
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (snapshot_date, signal_name) DO UPDATE SET
                      status = EXCLUDED.status,
                      value = EXCLUDED.value,
                      label = EXCLUDED.label,
                      reason = EXCLUDED.reason,
                      inputs = EXCLUDED.inputs,
                      metadata = EXCLUDED.metadata,
                      as_of = EXCLUDED.as_of
                    """,
                    (
                        snapshot_date,
                        result.name,
                        result.status,
                        result.value,
                        extract_label(result),
                        result.reason,
                        Json(result.inputs or {}),
                        Json(result.metadata or {}),
                        result.as_of,
                    ),
                )
                saved += 1
        return saved

    def load_for_date(self, snapshot_date: date) -> list[SignalSnapshotRow]:
        with connection_scope() as conn:
            rows = conn.execute(
                """
                SELECT snapshot_date, signal_name, status, value, label, reason,
                       inputs, metadata, as_of
                FROM signal_snapshots
                WHERE snapshot_date = %s
                ORDER BY signal_name
                """,
                (snapshot_date,),
            ).fetchall()
        return [self._row_to_snapshot(row) for row in rows]

    def load_previous_date(self, before: date) -> date | None:
        with connection_scope() as conn:
            row = conn.execute(
                """
                SELECT MAX(snapshot_date)
                FROM signal_snapshots
                WHERE snapshot_date < %s
                """,
                (before,),
            ).fetchone()
        if row is None or row[0] is None:
            return None
        return row[0]

    @staticmethod
    def _row_to_snapshot(row: tuple) -> SignalSnapshotRow:
        value = row[3]
        return SignalSnapshotRow(
            snapshot_date=row[0],
            signal_name=row[1],
            status=row[2],
            value=float(value) if value is not None else None,
            label=row[4],
            reason=row[5],
            inputs=dict(row[6] or {}),
            metadata=dict(row[7] or {}),
            as_of=row[8],
        )
