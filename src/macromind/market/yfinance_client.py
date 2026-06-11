from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class LatestBar:
    observation_date: date
    close: float
    metadata: dict[str, Any]


def parse_latest_bar(history: pd.DataFrame, *, symbol: str) -> LatestBar | None:
    if history is None or history.empty:
        return None

    frame = history.dropna(subset=["Close"])
    if frame.empty:
        return None

    last = frame.iloc[-1]
    idx = frame.index[-1]
    if hasattr(idx, "date"):
        obs_date = idx.date() if callable(getattr(idx, "date", None)) else idx
    elif isinstance(idx, date):
        obs_date = idx
    else:
        obs_date = pd.Timestamp(idx).date()

    close = float(last["Close"])
    prev_close: float | None = None
    if len(frame) >= 2:
        prev_close = float(frame.iloc[-2]["Close"])

    change_pct: float | None = None
    if prev_close is not None and prev_close != 0:
        change_pct = (close - prev_close) / prev_close * 100.0

    metadata: dict[str, Any] = {
        "ticker": symbol,
        "open": _optional_float(last, "Open"),
        "high": _optional_float(last, "High"),
        "low": _optional_float(last, "Low"),
        "volume": _optional_float(last, "Volume"),
        "prev_close": prev_close,
        "change_pct": change_pct,
    }
    return LatestBar(observation_date=obs_date, close=close, metadata=metadata)


def _optional_float(row: pd.Series, column: str) -> float | None:
    if column not in row.index:
        return None
    value = row[column]
    if pd.isna(value):
        return None
    return float(value)


class YFinanceClient:
    def get_bar_as_of(
        self, symbol: str, as_of: date, *, lookback_days: int = 14
    ) -> LatestBar | None:
        start = as_of - timedelta(days=lookback_days)
        end = as_of + timedelta(days=1)
        ticker = yf.Ticker(symbol)
        history = ticker.history(
            start=start.isoformat(),
            end=end.isoformat(),
            interval="1d",
            auto_adjust=True,
        )
        if history is None or history.empty:
            return None

        frame = history.dropna(subset=["Close"])
        if frame.empty:
            return None

        mask = [pd.Timestamp(idx).date() <= as_of for idx in frame.index]
        subset = frame.loc[mask]
        if subset.empty:
            return None
        return parse_latest_bar(subset, symbol=symbol)

    def get_latest_bar(self, symbol: str) -> LatestBar | None:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="5d", interval="1d", auto_adjust=True)
        bar = parse_latest_bar(history, symbol=symbol)
        if bar is None:
            return None

        info: dict[str, Any] = {}
        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        title = info.get("shortName") or info.get("longName")
        currency = info.get("currency")
        meta = dict(bar.metadata)
        if title:
            meta["title"] = title
        if currency:
            meta["currency"] = currency
        return LatestBar(
            observation_date=bar.observation_date,
            close=bar.close,
            metadata=meta,
        )
