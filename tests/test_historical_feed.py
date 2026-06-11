from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.historical_feed import (
    build_observations_as_of,
    filter_observations_as_of,
)


def _obs(series_key: str, observation_date: date, value: float) -> NormalizedObservation:
    return NormalizedObservation(
        source="fred",
        series_key=series_key,
        observation_date=observation_date,
        fetched_at=datetime(2020, 3, 16, 12, 0, tzinfo=timezone.utc),
        value_kind="level",
        value=value,
        unit="index",
        metadata={},
    )


def test_filter_observations_as_of_excludes_future_dates() -> None:
    observations = [
        _obs("UNRATE", date(2020, 4, 1), 4.4),
        _obs("UNRATE", date(2020, 3, 1), 3.5),
        _obs("UNRATE", date(2020, 5, 1), 14.7),
    ]
    filtered = filter_observations_as_of(observations, date(2020, 3, 16))
    dates = [obs.observation_date for obs in filtered]
    assert dates == [date(2020, 3, 1)]


def test_build_observations_as_of_fred_and_market(monkeypatch) -> None:
    as_of = date(2020, 3, 16)
    fetched_at = datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc)

    mock_fred = MagicMock()
    mock_fred.get_observations.return_value = [
        {"date": "2020-03-01", "value": "3.5"},
        {"date": "2020-02-01", "value": "3.6"},
    ]
    mock_fred.__enter__ = MagicMock(return_value=mock_fred)
    mock_fred.__exit__ = MagicMock(return_value=False)

    # Patch FredClient constructor path via injected client
    from macromind.market.yfinance_client import LatestBar

    mock_yf = MagicMock()
    mock_yf.get_bar_as_of.return_value = LatestBar(
        observation_date=as_of,
        close=240.0,
        metadata={"change_pct": -2.5, "ticker": "SPY"},
    )

    def fake_fetch(client, series_id, obs_date, ft):
        from macromind.models import DataPoint

        return [
            DataPoint(
                source="fred",
                indicator=series_id,
                value=3.5,
                unit="percent",
                period="2020-03-01",
                fetched_at=ft,
                metadata={"category": "employment"},
            )
        ]

    monkeypatch.setattr(
        "macromind.signals.historical_feed._fetch_fred_series",
        fake_fetch,
    )

    observations = build_observations_as_of(as_of, fred=mock_fred, yf=mock_yf)
    series_keys = {obs.series_key for obs in observations}
    assert "SPY" in series_keys
    assert "UNRATE" in series_keys
    assert all(obs.observation_date <= as_of for obs in observations)
