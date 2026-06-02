from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timezone

from macromind.db.repository import MacroRepository, PredictionMarketRepository


class _FakeCursor:
    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows

    def fetchall(self) -> list[tuple]:
        return self._rows


class _FakeConnection:
    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows

    def execute(self, _query: str):
        return _FakeCursor(self._rows)


def test_macro_repository_load_latest_datapoints(monkeypatch) -> None:
    rows = [
        (
            "fred",
            "DGS10",
            4.25,
            "percent",
            date(2026, 6, 1),
            datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
            "10-Year Treasury",
            "Daily",
            "rates",
        )
    ]

    @contextmanager
    def fake_scope():
        yield _FakeConnection(rows)

    monkeypatch.setattr("macromind.db.repository.connection_scope", fake_scope)
    result = MacroRepository().load_latest_datapoints()
    assert len(result) == 1
    assert result[0].indicator == "DGS10"
    assert result[0].metadata["category"] == "rates"


def test_prediction_market_repository_load_latest_snapshots(monkeypatch) -> None:
    rows = [
        (
            "kalshi",
            "KXCPIYOY",
            "inflation",
            "KXCPIYOY-26MAY",
            "KXCPIYOY-26MAY-T3.0",
            "threshold",
            "Above 3.0%",
            0.45,
            date(2026, 5, 1),
            datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
            None,
            3.0,
            "gt",
            "probability",
            "inflation",
            "Inflation",
            "Inflation Event",
            "2026-05",
            datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc),
            0.44,
            0.46,
            12000.0,
            "https://kalshi.com/markets/kxcpiyoy/inflation",
        )
    ]

    @contextmanager
    def fake_scope():
        yield _FakeConnection(rows)

    monkeypatch.setattr("macromind.db.repository.connection_scope", fake_scope)
    result = PredictionMarketRepository().load_latest_snapshots()
    assert len(result) == 1
    assert result[0].platform == "kalshi"
    assert result[0].macro_topic == "inflation"
    assert result[0].yes_probability == 0.45
