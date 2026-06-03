from __future__ import annotations

from unittest.mock import MagicMock

from macromind.crawlers.fred_crawler import FredCrawler
from macromind.macro.fred_watchlist import FredSeriesConfig


class _FakeRepo:
    def __init__(self, counts: dict[str, int]) -> None:
        self._counts = counts

    def count_observations(self, source: str, series_id: str) -> int:
        assert source == "fred"
        return self._counts.get(series_id, 0)


def test_fetch_one_uses_bootstrap_limit_when_db_sparse() -> None:
    client = MagicMock()
    client.get_observations.return_value = [
        {"date": "2026-01-01", "value": "100"},
        {"date": "2025-12-01", "value": "99"},
    ]
    repo = _FakeRepo({"WALCL": 0})
    config = FredSeriesConfig(
        series_id="WALCL",
        category="liquidity",
        unit="millions_usd",
        min_points=2,
        bootstrap_limit=15,
        steady_limit=5,
    )
    crawler = FredCrawler()
    points = crawler._fetch_one(client, repo, config, "WALCL")

    client.get_observations.assert_called_once_with("WALCL", limit=15, sort_order="desc")
    assert len(points) == 2
    assert points[0].indicator == "WALCL"
    assert points[0].period == "2026-01-01"
    assert points[0].value == 100.0


def test_fetch_one_uses_steady_limit_when_db_sufficient() -> None:
    client = MagicMock()
    client.get_observations.return_value = [
        {"date": "2026-06-01", "value": "300"},
    ]
    repo = _FakeRepo({"CPIAUCSL": 13})
    config = FredSeriesConfig(
        series_id="CPIAUCSL",
        category="inflation",
        unit="index",
        min_points=13,
        bootstrap_limit=15,
        steady_limit=5,
    )
    crawler = FredCrawler()
    points = crawler._fetch_one(client, repo, config, "CPIAUCSL")

    client.get_observations.assert_called_once_with("CPIAUCSL", limit=5, sort_order="desc")
    assert len(points) == 1


def test_macro_repository_count_observations(monkeypatch) -> None:
    from contextlib import contextmanager

    from macromind.db.repository import MacroRepository

    class _FakeCursor:
        def fetchone(self):
            return (7,)

    class _FakeConnection:
        def execute(self, _query: str, _params: tuple):
            return _FakeCursor()

    @contextmanager
    def fake_scope():
        yield _FakeConnection()

    monkeypatch.setattr("macromind.db.repository.connection_scope", fake_scope)
    assert MacroRepository().count_observations("fred", "UNRATE") == 7
