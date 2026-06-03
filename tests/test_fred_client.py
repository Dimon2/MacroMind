from datetime import date

import httpx

from macromind.macro.fred_client import (
    _retry_after_seconds,
    parse_latest_observation,
    parse_observations,
)


def test_parse_latest_observation_skips_missing() -> None:
    observations = [
        {"date": "2026-05-30", "value": "."},
        {"date": "2026-05-29", "value": "4.25"},
    ]
    result = parse_latest_observation(observations)
    assert result == (date(2026, 5, 29), 4.25)


def test_parse_latest_observation_first_valid() -> None:
    observations = [
        {"date": "2026-05-31", "value": "3.1"},
        {"date": "2026-05-30", "value": "3.0"},
    ]
    result = parse_latest_observation(observations)
    assert result == (date(2026, 5, 31), 3.1)


def test_parse_latest_observation_empty() -> None:
    assert parse_latest_observation([]) is None
    assert parse_latest_observation([{"date": "2026-01-01", "value": "."}]) is None


def test_parse_observations_skips_missing_and_returns_all_valid() -> None:
    observations = [
        {"date": "2026-05-30", "value": "."},
        {"date": "2026-05-29", "value": "4.25"},
        {"date": "2026-05-28", "value": "4.20"},
    ]
    result = parse_observations(observations)
    assert len(result) == 2
    assert result[0] == (date(2026, 5, 29), 4.25)
    assert result[1] == (date(2026, 5, 28), 4.20)


def test_retry_after_seconds_honors_header() -> None:
    response = httpx.Response(429, headers={"Retry-After": "30"})
    assert _retry_after_seconds(response, 0) == 30.0


def test_retry_after_seconds_exponential_fallback() -> None:
    response = httpx.Response(429)
    assert _retry_after_seconds(response, 0) == 15.0
    assert _retry_after_seconds(response, 2) == 60.0
    assert _retry_after_seconds(response, 10) == 120.0
