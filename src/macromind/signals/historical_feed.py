from __future__ import annotations

from datetime import date, datetime, time, timezone

from macromind.macro.fred_client import FredClient, parse_observations
from macromind.market.normalized_observation import NormalizedObservation
from macromind.market.normalizers import normalize_macro_datapoint
from macromind.market.yfinance_client import YFinanceClient
from macromind.models import DataPoint
from macromind.signals.regime_series import REGIME_SERIES_IDS

FRED_SOURCE = "fred"
YFINANCE_SOURCE = "yfinance"

FRED_LAB_SERIES: tuple[str, ...] = (
    *REGIME_SERIES_IDS,
    "T10Y2Y",
    "DGS10",
    "DGS2",
)

CREDIT_HY_SERIES_PRIMARY = "BAMLH0A0HYM2"
CREDIT_HY_SERIES_FALLBACK = "BAMLC0A4CBBBEY"

FRED_MONTHLY_SERIES: frozenset[str] = frozenset(
    {"CPIAUCSL", "CPILFESL", "UNRATE", "M2SL"}
)
FRED_MONTHLY_LIMIT = 24
FRED_WEEKLY_LIMIT = 60

_FRED_SERIES_META: dict[str, tuple[str, str]] = {
    "CPIAUCSL": ("index", "inflation"),
    "CPILFESL": ("index", "inflation"),
    "UNRATE": ("percent", "employment"),
    "WALCL": ("millions_usd", "liquidity"),
    "RRPONTSYD": ("billions_usd", "liquidity"),
    "WTREGEN": ("millions_usd", "liquidity"),
    "M2SL": ("billions_usd", "liquidity"),
    "T10Y2Y": ("percent", "rates"),
    "DGS10": ("percent", "rates"),
    "DGS2": ("percent", "rates"),
    CREDIT_HY_SERIES_PRIMARY: ("percent", "credit"),
    CREDIT_HY_SERIES_FALLBACK: ("percent", "credit"),
}

MARKET_LAB_SYMBOLS: tuple[tuple[str, str], ...] = (
    ("SPY", "SPY"),
    ("VIX", "^VIX"),
    ("HYG", "HYG"),
)

_MARKET_UNITS: dict[str, str] = {
    "SPY": "usd",
    "VIX": "index",
    "HYG": "usd",
}


def filter_observations_as_of(
    observations: list[NormalizedObservation],
    as_of: date,
) -> list[NormalizedObservation]:
    filtered = [obs for obs in observations if obs.observation_date <= as_of]
    return sorted(filtered, key=lambda item: (item.observation_date, item.source, item.series_key))


def build_observations_as_of(
    as_of: date,
    *,
    fred: FredClient | None = None,
    yf: YFinanceClient | None = None,
) -> list[NormalizedObservation]:
    fetched_at = datetime.combine(as_of, time(23, 59, 59), tzinfo=timezone.utc)
    datapoints: list[DataPoint] = []

    with _fred_client(fred) as client:
        for series_id in FRED_LAB_SERIES:
            datapoints.extend(_fetch_fred_series(client, series_id, as_of, fetched_at))
        datapoints.extend(_fetch_credit_hy_series(client, as_of, fetched_at))

    yf_client = yf or YFinanceClient()
    for indicator, symbol in MARKET_LAB_SYMBOLS:
        bar = yf_client.get_bar_as_of(symbol, as_of)
        if bar is None:
            continue
        datapoints.append(
            DataPoint(
                source=YFINANCE_SOURCE,
                indicator=indicator,
                value=bar.close,
                unit=_MARKET_UNITS[indicator],
                period=bar.observation_date.isoformat(),
                fetched_at=fetched_at,
                metadata={"category": "equity" if indicator in ("SPY", "HYG") else "sentiment", **bar.metadata},
            )
        )

    return [normalize_macro_datapoint(dp) for dp in datapoints]


def _fred_client(existing: FredClient | None):
    if existing is not None:
        return _NoCloseFred(existing)
    return FredClient()


class _NoCloseFred:
    def __init__(self, client: FredClient) -> None:
        self._client = client

    def __enter__(self) -> FredClient:
        return self._client

    def __exit__(self, *args: object) -> None:
        return None


def _fetch_credit_hy_series(
    client: FredClient,
    as_of: date,
    fetched_at: datetime,
) -> list[DataPoint]:
    for series_id in (CREDIT_HY_SERIES_PRIMARY, CREDIT_HY_SERIES_FALLBACK):
        rows = _fetch_fred_series(client, series_id, as_of, fetched_at)
        if not rows:
            continue
        if series_id == CREDIT_HY_SERIES_PRIMARY:
            return rows
        return [
            DataPoint(
                source=row.source,
                indicator=CREDIT_HY_SERIES_PRIMARY,
                value=row.value,
                unit=row.unit,
                period=row.period,
                fetched_at=row.fetched_at,
                metadata={
                    **row.metadata,
                    "resolved_series_id": series_id,
                    "requested_series_id": CREDIT_HY_SERIES_PRIMARY,
                },
            )
            for row in rows
        ]
    return []


def _fetch_fred_series(
    client: FredClient,
    series_id: str,
    as_of: date,
    fetched_at: datetime,
) -> list[DataPoint]:
    limit = FRED_MONTHLY_LIMIT if series_id in FRED_MONTHLY_SERIES else FRED_WEEKLY_LIMIT
    unit, category = _FRED_SERIES_META[series_id]
    raw = client.get_observations(
        series_id,
        limit=limit,
        sort_order="desc",
        observation_end=as_of,
    )
    parsed = parse_observations(raw)
    rows = [(obs_date, value) for obs_date, value in parsed if obs_date <= as_of]
    rows = rows[:limit]

    return [
        DataPoint(
            source=FRED_SOURCE,
            indicator=series_id,
            value=value,
            unit=unit,
            period=obs_date.isoformat(),
            fetched_at=fetched_at,
            metadata={"category": category},
        )
        for obs_date, value in rows
    ]
