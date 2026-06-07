from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from macromind.api.app import create_app

_NOW = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health_db_ok(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("macromind.api.read.health.ping_db", lambda: True)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert "freshness" not in body


def test_health_db_error(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("macromind.api.read.health.ping_db", lambda: False)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["db"] == "error"


def test_health_with_freshness(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("macromind.api.read.health.ping_db", lambda: True)
    monkeypatch.setattr(
        "macromind.api.read.health.build_crawl_status",
        lambda _names: {"as_of": _NOW.isoformat(), "crawlers": {}, "missing": []},
    )
    monkeypatch.setattr(
        "macromind.api.read.health.crawl_status_is_healthy",
        lambda _status, _names: False,
    )
    response = client.get("/health?freshness=true")
    assert response.status_code == 200
    body = response.json()
    assert body["healthy"] is False
    assert "freshness" in body
