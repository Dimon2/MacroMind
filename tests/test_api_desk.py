from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from macromind.api.app import create_app
from macromind.api.read.desk import NoSnapshotsError, load_latest_desk
from macromind.db.signal_snapshot import SignalSnapshotRow
from macromind.models import DataPoint

_NOW = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)
_DAY = date(2026, 6, 6)
_PREV = date(2026, 6, 5)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _row(
    name: str,
    *,
    value: float | None = 1.0,
    label: str | None = None,
    inputs: dict | None = None,
) -> SignalSnapshotRow:
    return SignalSnapshotRow(
        snapshot_date=_DAY,
        signal_name=name,
        status="computed",
        value=value,
        label=label,
        reason=None,
        inputs=inputs or {},
        metadata={"label": label} if label else {},
        as_of=_NOW,
    )


def test_load_latest_desk_raises_when_empty() -> None:
    repo = MagicMock()
    repo.load_latest_snapshots.return_value = []
    with pytest.raises(NoSnapshotsError):
        load_latest_desk(snapshot_repo=repo)


def test_load_latest_desk_cards_shape() -> None:
    repo = MagicMock()
    repo.load_latest_snapshots.return_value = [
        _row("risk_regime", label="risk_on"),
        _row(
            "liquidity_regime",
            label="easy",
            inputs={
                "net_liquidity": 7_000_000.0,
                "net_liquidity_change_wow_pct": 0.3,
                "net_liquidity_date": "2026-06-06",
                "M2SL_latest": 22800.0,
                "M2SL_change_mom_pct": 0.4,
                "M2SL_yoy_pct": 1.5,
                "M2SL_yoy_status": "computed",
            },
        ),
        _row("inflation_regime", label="stable", value=3.0),
        _row(
            "growth_regime",
            label="expanding",
            inputs={"curve_spread": 0.25, "curve_state": "normal", "curve_source": "T10Y2Y"},
        ),
        _row("credit_regime", label="normal", value=4.0),
        _row("market_state", label="risk_on_easy_stable_expanding_normal", value=None),
        _row("inflation_pm_overlay", value=None, inputs={"markets": [{"yes_probability": 0.4}]}),
        _row(
            "fed_rate_context",
            value=None,
            inputs={"effective_rate": 4.25, "kalshi_markets": []},
        ),
    ]
    repo.load_previous_date.return_value = _PREV
    repo.load_for_date.return_value = [_row("risk_regime", value=0.5, label="neutral")]

    macro_repo = MagicMock()
    macro_repo.load_latest_datapoints.return_value = [
        DataPoint("yfinance", "SPY", 500.0, "usd", "2026-06-06", _NOW, {"change_pct": 0.5}),
        DataPoint("yfinance", "VIX", 18.0, "index", "2026-06-06", _NOW, {}),
    ]

    result = load_latest_desk(snapshot_repo=repo, macro_repo=macro_repo)
    assert result["snapshot_date"] == "2026-06-06"
    assert result["deterministic"] is True
    assert "risk" in result["cards"]
    assert result["cards"]["liquidity"]["m2"]["yoy_pct"] == 1.5
    assert result["cards"]["growth"]["curve"]["curve_state"] == "normal"
    assert result["overlays"]["fed_compare"]["effective_rate"] == 4.25


def test_desk_latest_endpoint_404(client: TestClient, monkeypatch) -> None:
    def raise_no_snapshots():
        raise NoSnapshotsError()

    monkeypatch.setattr("macromind.api.app.load_latest_desk", raise_no_snapshots)
    response = client.get("/desk/latest")
    assert response.status_code == 404


def test_desk_latest_endpoint(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        "macromind.api.app.load_latest_desk",
        lambda: {
            "schema_version": "1.0",
            "deterministic": True,
            "snapshot_date": "2026-06-06",
            "as_of": _NOW.isoformat(),
            "composite": "risk_on",
            "cards": {},
            "overlays": {},
            "deltas": [],
            "previous_snapshot_date": None,
            "details": {"signals": []},
        },
    )
    response = client.get("/desk/latest")
    assert response.status_code == 200
    assert response.json()["snapshot_date"] == "2026-06-06"


def test_signals_latest_removed(client: TestClient) -> None:
    response = client.get("/signals/latest")
    assert response.status_code == 404
