from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from macromind.api.app import create_app
from macromind.api.read.macro import SeriesNotFoundError, load_macro_series
from macromind.models import DataPoint

_NOW = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _dp(*, period: str, value: float) -> DataPoint:
    return DataPoint(
        source="fred",
        indicator="DGS10",
        value=value,
        unit="percent",
        period=period,
        fetched_at=_NOW,
        metadata={"title": "10-Year Treasury", "frequency": "Daily", "category": "rates"},
    )


def test_load_macro_series_raises_when_empty() -> None:
    repo = MagicMock()
    repo.load_observations.return_value = []
    with pytest.raises(SeriesNotFoundError):
        load_macro_series("DGS10", macro_repo=repo)


def test_load_macro_series_returns_n_points() -> None:
    repo = MagicMock()
    repo.load_observations.return_value = [
        _dp(period="2026-06-05", value=4.25),
        _dp(period="2026-06-04", value=4.2),
    ]
    result = load_macro_series("dgs10", limit=2, macro_repo=repo)
    repo.load_observations.assert_called_once_with("fred", ["DGS10"], last_n=2)
    assert result["series_id"] == "DGS10"
    assert result["count"] == 2
    assert result["observations"][0]["observation_date"] == "2026-06-05"


def test_load_macro_series_clamps_limit() -> None:
    repo = MagicMock()
    repo.load_observations.return_value = [_dp(period="2026-06-05", value=4.25)]
    load_macro_series("DGS10", limit=999, macro_repo=repo)
    repo.load_observations.assert_called_once_with("fred", ["DGS10"], last_n=500)


def test_macro_endpoint_404(client: TestClient, monkeypatch) -> None:
    def raise_not_found(series_id: str, **kwargs):
        raise SeriesNotFoundError()

    monkeypatch.setattr("macromind.api.app.load_macro_series", raise_not_found)
    response = client.get("/macro/DGS10")
    assert response.status_code == 404


def test_macro_endpoint(client: TestClient, monkeypatch) -> None:
    repo = MagicMock()
    repo.load_observations.return_value = [_dp(period="2026-06-05", value=4.25)]

    monkeypatch.setattr(
        "macromind.api.app.load_macro_series",
        lambda series_id, **kwargs: load_macro_series(series_id, macro_repo=repo, **kwargs),
    )
    response = client.get("/macro/DGS10?limit=5")
    assert response.status_code == 200
    assert response.json()["count"] == 1
