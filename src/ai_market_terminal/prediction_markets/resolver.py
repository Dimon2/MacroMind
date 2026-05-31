from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ai_market_terminal.prediction_markets.kalshi_client import KalshiClient
from ai_market_terminal.prediction_markets.models import PredictionMarketSnapshot
from ai_market_terminal.prediction_markets.outcome import parse_outcome, parse_reference_period
from ai_market_terminal.prediction_markets.watchlist import SeriesWatchConfig


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _to_probability(market: dict[str, Any]) -> tuple[float, float | None, float | None]:
    yes_bid = _price_to_prob(market.get("yes_bid"))
    yes_ask = _price_to_prob(market.get("yes_ask"))

    if yes_bid is not None and yes_ask is not None:
        return (yes_bid + yes_ask) / 2, yes_bid, yes_ask

    for key in ("last_price", "yes_price"):
        if (prob := _price_to_prob(market.get(key))) is not None:
            return prob, yes_bid, yes_ask

    for key in ("yes_bid_dollars", "yes_ask_dollars"):
        if market.get("yes_bid_dollars") is not None or market.get("yes_ask_dollars") is not None:
            bid = _dollar_to_prob(market.get("yes_bid_dollars"))
            ask = _dollar_to_prob(market.get("yes_ask_dollars"))
            if bid is not None and ask is not None:
                return (bid + ask) / 2, bid, ask
            if bid is not None:
                return bid, bid, ask
            if ask is not None:
                return ask, bid, ask

    if (last := _dollar_to_prob(market.get("last_price_dollars"))) is not None:
        bid = _dollar_to_prob(market.get("yes_bid_dollars")) or yes_bid
        ask = _dollar_to_prob(market.get("yes_ask_dollars")) or yes_ask
        return last, bid, ask

    return 0.0, yes_bid, yes_ask


def _price_to_prob(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric > 1:
        return numeric / 100
    return numeric


def _dollar_to_prob(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _volume(market: dict[str, Any]) -> float | None:
    for key in ("volume_fp", "volume", "volume_24h_fp", "volume_24h"):
        if market.get(key) is not None:
            try:
                return float(market[key])
            except (TypeError, ValueError):
                continue
    return None


def _outcome_label(market: dict[str, Any]) -> str:
    for key in ("yes_sub_title", "subtitle", "title"):
        if market.get(key):
            return str(market[key])
    return market.get("ticker", "unknown")


def _market_url(series_slug: str | None, market_ticker: str, series_ticker: str) -> str:
    slug = series_slug or series_ticker.lower()
    return f"https://kalshi.com/markets/{series_ticker.lower()}/{slug}/{market_ticker.lower()}"


class EventMarketResolver:
    def __init__(self, client: KalshiClient) -> None:
        self._client = client

    def resolve_series(self, config: SeriesWatchConfig) -> list[PredictionMarketSnapshot]:
        series_ticker = config.series_ticker.upper()
        series_slug = config.slug

        markets = self._client.list_markets(series_ticker=series_ticker)
        if not markets:
            print(f"[kalshi] No open markets for {series_ticker}")
            return []

        event_ticker = self._resolve_event_ticker(markets)
        event_markets = [m for m in markets if m.get("event_ticker", "").upper() == event_ticker]
        if not event_markets:
            event_markets = markets

        first = event_markets[0]
        event_title = first.get("event_title") or first.get("title")
        event_close = _parse_dt(first.get("close_time") or first.get("expiration_time"))
        reference_period = parse_reference_period(
            str(event_title) if event_title else None,
            None,
        )

        selected = self._select_markets(config, event_markets)
        now = datetime.now(timezone.utc)
        period = now.date()
        event_url = _market_url(series_slug, event_ticker, series_ticker).rsplit("/", 1)[0]

        snapshots: list[PredictionMarketSnapshot] = []
        for market in selected:
            label = _outcome_label(market)
            parsed = parse_outcome(label)
            yes_prob, yes_bid, yes_ask = _to_probability(market)
            market_ticker = str(market["ticker"]).upper()

            snapshots.append(
                PredictionMarketSnapshot(
                    platform="kalshi",
                    series_ticker=series_ticker,
                    macro_topic=config.macro_topic,
                    event_ticker=event_ticker,
                    market_ticker=market_ticker,
                    outcome_type=parsed.outcome_type,
                    outcome_label=parsed.outcome_label,
                    yes_probability=yes_prob,
                    period_date=period,
                    fetched_at=now,
                    outcome_key=parsed.outcome_key,
                    strike=parsed.strike,
                    strike_op=parsed.strike_op,
                    unit_hint=parsed.unit_hint,
                    series_slug=series_slug,
                    series_title=None,
                    event_title=str(event_title) if event_title else None,
                    reference_period=reference_period,
                    event_close_at=event_close,
                    yes_bid=yes_bid,
                    yes_ask=yes_ask,
                    volume=_volume(market),
                    url=_market_url(series_slug, market_ticker, series_ticker),
                    metadata={"status": market.get("status")},
                )
            )

        print(
            f"[kalshi] {series_ticker}: event={event_ticker} "
            f"markets={len(snapshots)}/{len(event_markets)} url={event_url}"
        )
        return snapshots

    def _resolve_event_ticker(self, markets: list[dict[str, Any]]) -> str:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for market in markets:
            key = str(market.get("event_ticker", "")).upper()
            grouped.setdefault(key, []).append(market)

        best_ticker = ""
        best_score: tuple[int, float] | None = None
        now = datetime.now(timezone.utc)

        for event_ticker, event_markets in grouped.items():
            if not event_ticker:
                continue
            close_times = [
                t
                for t in (_parse_dt(m.get("close_time")) for m in event_markets)
                if t is not None
            ]
            future_times = [t for t in close_times if t >= now]
            if future_times:
                nearest = min(future_times, key=lambda t: (t - now).total_seconds())
                score = (0, (nearest - now).total_seconds())
            elif close_times:
                nearest = max(close_times)
                score = (1, -(nearest.timestamp()))
            else:
                total_volume = sum(_volume(m) or 0 for m in event_markets)
                score = (2, -total_volume)

            if best_score is None or score < best_score:
                best_score = score
                best_ticker = event_ticker

        return best_ticker or str(markets[0].get("event_ticker", "")).upper()

    def _select_markets(
        self, config: SeriesWatchConfig, markets: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if config.market_mode == "all":
            return markets

        def atm_distance(market: dict[str, Any]) -> float:
            prob, _, _ = _to_probability(market)
            return abs(prob - 0.5)

        ranked = sorted(markets, key=atm_distance)
        return ranked[: config.max_markets]
