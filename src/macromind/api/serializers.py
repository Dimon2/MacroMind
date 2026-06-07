from __future__ import annotations

from typing import Any

from macromind.db.signal_snapshot import SignalSnapshotRow
from macromind.models import DataPoint

SCHEMA_VERSION = "1.0"


def snapshot_row_to_signal_dict(row: SignalSnapshotRow) -> dict[str, Any]:
    return {
        "name": row.signal_name,
        "status": row.status,
        "value": row.value,
        "reason": row.reason,
        "inputs": row.inputs,
        "metadata": row.metadata,
        "as_of": row.as_of.isoformat(),
    }


def datapoint_to_observation_dict(dp: DataPoint) -> dict[str, Any]:
    return {
        "observation_date": dp.period,
        "value": dp.value,
        "unit": dp.unit,
        "fetched_at": dp.fetched_at.isoformat(),
    }
