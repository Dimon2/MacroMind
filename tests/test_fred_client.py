from datetime import date

from ai_market_terminal.macro.fred_client import parse_latest_observation


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
