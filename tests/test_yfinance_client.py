from datetime import date

import pandas as pd
import pytest

from macromind.market.yfinance_client import parse_latest_bar


def test_parse_latest_bar_uses_last_trading_row() -> None:
    history = pd.DataFrame(
        {
            "Open": [10.0, 11.0, 12.0],
            "High": [10.5, 11.5, 12.5],
            "Low": [9.5, 10.5, 11.5],
            "Close": [10.0, 11.0, 13.0],
            "Volume": [100.0, 200.0, 300.0],
        },
        index=pd.to_datetime(["2026-05-27", "2026-05-28", "2026-05-29"]),
    )
    result = parse_latest_bar(history, symbol="^VIX")
    assert result is not None
    assert result.observation_date == date(2026, 5, 29)
    assert result.close == 13.0
    assert result.metadata["ticker"] == "^VIX"
    assert result.metadata["prev_close"] == 11.0
    assert result.metadata["change_pct"] == pytest.approx(18.181818, rel=1e-3)


def test_parse_latest_bar_skips_nan_close() -> None:
    history = pd.DataFrame(
        {"Close": [float("nan"), 5.0]},
        index=pd.to_datetime(["2026-05-30", "2026-05-29"]),
    )
    result = parse_latest_bar(history, symbol="SPY")
    assert result is not None
    assert result.close == 5.0
    assert result.observation_date == date(2026, 5, 29)


def test_parse_latest_bar_empty() -> None:
    assert parse_latest_bar(pd.DataFrame(), symbol="SPY") is None
