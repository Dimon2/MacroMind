from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timezone

from macromind.db.signal_snapshot import SignalSnapshotRepository, extract_label
from macromind.signals.models import SignalResult

_NOW = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)
_DAY = date(2026, 6, 2)


class _RecordingCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple | None]] = []
        self._fetch_rows: list[tuple] = []
        self._fetchone: tuple | None = None

    def fetchall(self) -> list[tuple]:
        return self._fetch_rows

    def fetchone(self) -> tuple | None:
        return self._fetchone


class _RecordingConnection:
    def __init__(self) -> None:
        self.cursor = _RecordingCursor()

    def execute(self, query: str, params: tuple | None = None):
        self.cursor.executed.append((query, params))
        return self.cursor


def test_extract_label_risk_regime() -> None:
    result = SignalResult(
        name="risk_regime",
        status="computed",
        value=1.0,
        metadata={"label": "risk_on"},
        as_of=_NOW,
    )
    assert extract_label(result) == "risk_on"


def test_extract_label_curve_state() -> None:
    result = SignalResult(
        name="rates_curve_proxy",
        status="computed",
        value=-0.5,
        metadata={"curve_state": "inverted"},
        as_of=_NOW,
    )
    assert extract_label(result) == "inverted"


def test_upsert_for_date_inserts(monkeypatch) -> None:
    conn = _RecordingConnection()

    @contextmanager
    def fake_scope():
        yield conn

    monkeypatch.setattr("macromind.db.signal_snapshot.connection_scope", fake_scope)
    repo = SignalSnapshotRepository()
    count = repo.upsert_for_date(
        _DAY,
        [
            SignalResult(
                name="risk_regime",
                status="computed",
                value=1.0,
                metadata={"label": "risk_on"},
                as_of=_NOW,
            )
        ],
    )
    assert count == 1
    query, params = conn.cursor.executed[0]
    assert "ON CONFLICT" in query
    assert params[0] == _DAY
    assert params[1] == "risk_regime"


def test_load_previous_date(monkeypatch) -> None:
    conn = _RecordingConnection()
    conn.cursor._fetchone = (date(2026, 6, 1),)

    @contextmanager
    def fake_scope():
        yield conn

    monkeypatch.setattr("macromind.db.signal_snapshot.connection_scope", fake_scope)
    result = SignalSnapshotRepository().load_previous_date(_DAY)
    assert result == date(2026, 6, 1)
