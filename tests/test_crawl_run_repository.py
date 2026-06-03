from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

from macromind.db.crawl_run import CrawlRunRecord
from macromind.db.repository import CrawlRunRepository

_NOW = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)


class _RecordingCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple | None]] = []
        self._fetch_rows: list[tuple] = []

    def fetchall(self) -> list[tuple]:
        return self._fetch_rows


class _RecordingConnection:
    def __init__(self) -> None:
        self.cursor = _RecordingCursor()

    def execute(self, query: str, params: tuple | None = None):
        self.cursor.executed.append((query, params))
        return self.cursor


def test_record_run_inserts_row(monkeypatch) -> None:
    conn = _RecordingConnection()

    @contextmanager
    def fake_scope():
        yield conn

    monkeypatch.setattr("macromind.db.repository.connection_scope", fake_scope)
    repo = CrawlRunRepository()
    repo.record_run(
        CrawlRunRecord(
            crawler="fred",
            started_at=_NOW,
            finished_at=_NOW,
            status="success",
            rows_persisted=12,
        )
    )
    assert len(conn.cursor.executed) == 1
    _query, params = conn.cursor.executed[0]
    assert "INSERT INTO crawl_runs" in _query
    assert params[0] == "fred"
    assert params[3] == "success"
    assert params[4] == 12


def test_load_last_success_by_crawler(monkeypatch) -> None:
    rows = [
        (
            "fred",
            _NOW,
            _NOW,
            "success",
            10,
            None,
        )
    ]
    conn = _RecordingConnection()
    conn.cursor._fetch_rows = rows

    @contextmanager
    def fake_scope():
        yield conn

    monkeypatch.setattr("macromind.db.repository.connection_scope", fake_scope)
    result = CrawlRunRepository().load_last_success_by_crawler()
    assert "fred" in result
    assert result["fred"].rows_persisted == 10
    query, _params = conn.cursor.executed[0]
    assert "status = %s" in query
