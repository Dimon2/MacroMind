from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from macromind.api.app import create_app
from macromind.api.read.signals import NoSnapshotsError, load_latest_signals
from macromind.db.signal_snapshot import SignalSnapshotRow

_NOW = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)
_DAY = date(2026, 6, 6)
_PREV = date(2026, 6, 5)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _row(name: str, *, value: float = 1.0) -> SignalSnapshotRow:
    return SignalSnapshotRow(
        snapshot_date=_DAY,
        signal_name=name,
        status="computed",
        value=value,
        label="risk_on" if name == "risk_regime" else None,
        reason=None,
        inputs={},
        metadata={"label": "risk_on"} if name == "risk_regime" else {},
        as_of=_NOW,
    )


def test_load_latest_signals_raises_when_empty() -> None:
    repo = MagicMock()
    repo.load_latest_date.return_value = None
    with pytest.raises(NoSnapshotsError):
        load_latest_signals(snapshot_repo=repo)


def test_load_latest_signals_shape() -> None:
    repo = MagicMock()
    repo.load_latest_date.return_value = _DAY
    repo.load_for_date.return_value = [_row("risk_regime")]
    repo.load_previous_date.return_value = _PREV
    repo.load_for_date.side_effect = lambda d: [_row("risk_regime", value=1.0 if d == _DAY else 0.5)]

    result = load_latest_signals(snapshot_repo=repo)
    assert result["snapshot_date"] == "2026-06-06"
    assert result["deterministic"] is True
    assert result["signals"][0]["name"] == "risk_regime"
    assert result["previous_snapshot_date"] == "2026-06-05"
    assert len(result["deltas"]) == 1


def test_signals_latest_endpoint_404(client: TestClient, monkeypatch) -> None:
    def raise_no_snapshots():
        raise NoSnapshotsError()

    monkeypatch.setattr("macromind.api.app.load_latest_signals", raise_no_snapshots)
    response = client.get("/signals/latest")
    assert response.status_code == 404


def test_signals_latest_endpoint(client: TestClient, monkeypatch) -> None:
    repo = MagicMock()
    repo.load_latest_date.return_value = _DAY
    repo.load_for_date.side_effect = lambda d: [_row("risk_regime", value=1.0 if d == _DAY else 0.5)]
    repo.load_previous_date.return_value = _PREV

    monkeypatch.setattr(
        "macromind.api.app.load_latest_signals",
        lambda: load_latest_signals(snapshot_repo=repo),
    )
    response = client.get("/signals/latest")
    assert response.status_code == 200
    assert response.json()["signals"][0]["name"] == "risk_regime"
