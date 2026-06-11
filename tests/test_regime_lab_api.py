from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from macromind.api.app import create_app
from macromind.api.read.regime_lab import compute_regime_lab
from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals import regime_lab_cache

_FETCHED = datetime(2020, 3, 16, 23, 59, 59, tzinfo=timezone.utc)
_QUERY = date(2020, 3, 16)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def clear_lab_cache() -> None:
    regime_lab_cache.clear()
    yield
    regime_lab_cache.clear()


def _risk_observations() -> list[NormalizedObservation]:
    return [
        NormalizedObservation(
            source="yfinance",
            series_key="SPY",
            observation_date=_QUERY,
            fetched_at=_FETCHED,
            value_kind="level",
            value=240.0,
            unit="usd",
            metadata={"change_pct": -5.0},
        ),
        NormalizedObservation(
            source="yfinance",
            series_key="VIX",
            observation_date=_QUERY,
            fetched_at=_FETCHED,
            value_kind="level",
            value=82.0,
            unit="index",
            metadata={},
        ),
        NormalizedObservation(
            source="fred",
            series_key="BAMLH0A0HYM2",
            observation_date=_QUERY,
            fetched_at=_FETCHED,
            value_kind="rate",
            value=8.5,
            unit="percent",
            metadata={"category": "credit"},
        ),
    ]


def test_lab_regime_episodes(client: TestClient) -> None:
    response = client.get("/lab/regime/episodes")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 10
    assert body["episodes"][0]["date"] == "2008-09-15"
    assert body["episodes"][0]["phase"] == "detection"


def test_lab_regime_compute_mocked(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        "macromind.api.read.regime_lab.build_observations_as_of",
        lambda _as_of, **_: _risk_observations(),
    )
    response = client.get("/lab/regime/compute", params={"date": "2020-03-16"})
    assert response.status_code == 200
    body = response.json()
    assert body["query_date"] == "2020-03-16"
    assert body["episode"]["note"] == "COVID panic"
    assert body["cards"]["risk"]["regime"]["label"] == "risk_off"
    assert body["cards"]["credit"]["regime"]["label"] == "stressed"
    assert "signals" in body
    assert body["coverage"]["total"] == 8


def test_lab_regime_compute_invalid_date(client: TestClient) -> None:
    response = client.get("/lab/regime/compute", params={"date": "not-a-date"})
    assert response.status_code == 400


def test_lab_regime_compute_future_date(client: TestClient) -> None:
    response = client.get("/lab/regime/compute", params={"date": "2099-01-01"})
    assert response.status_code == 400


def test_lab_regime_compute_cache_hit(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_build(as_of, **kwargs):
        calls["n"] += 1
        return _risk_observations()

    monkeypatch.setattr(
        "macromind.api.read.regime_lab.build_observations_as_of",
        fake_build,
    )
    first = compute_regime_lab(_QUERY)
    second = compute_regime_lab(_QUERY)
    assert first["query_date"] == second["query_date"]
    assert calls["n"] == 1


def test_lab_regime_compute_custom_date_no_episode(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        "macromind.api.read.regime_lab.build_observations_as_of",
        lambda _as_of, **_: _risk_observations(),
    )
    response = client.get("/lab/regime/compute", params={"date": "2019-06-01"})
    assert response.status_code == 200
    assert response.json()["episode"] is None
