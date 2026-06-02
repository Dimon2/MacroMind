from datetime import date
from unittest.mock import MagicMock, patch

from macromind.crawlers.market_crawler import MarketCrawler
from macromind.market.market_watchlist import MarketTickerConfig
from macromind.market.yfinance_client import LatestBar


def test_bar_to_datapoint_uses_observation_date() -> None:
    crawler = MarketCrawler()
    config = MarketTickerConfig(
        indicator="VIX",
        symbol="^VIX",
        category="sentiment",
        unit="index",
    )
    bar = LatestBar(
        observation_date=date(2026, 5, 29),
        close=18.5,
        metadata={"ticker": "^VIX", "volume": 0.0},
    )
    dp = crawler._bar_to_datapoint(config, bar, resolved_symbol="^VIX")
    assert dp.source == "yfinance"
    assert dp.indicator == "VIX"
    assert dp.value == 18.5
    assert dp.period == "2026-05-29"
    assert dp.metadata["category"] == "sentiment"


def test_fetch_ticker_uses_fallback() -> None:
    crawler = MarketCrawler()
    config = MarketTickerConfig(
        indicator="DXY",
        symbol="DX-Y.NYB",
        fallback_symbol="UUP",
        category="fx",
        unit="index",
    )
    client = MagicMock()
    client.get_latest_bar.side_effect = [
        None,
        LatestBar(
            observation_date=date(2026, 5, 29),
            close=28.1,
            metadata={"ticker": "UUP"},
        ),
    ]
    dp = crawler._fetch_ticker(client, config)
    assert dp is not None
    assert dp.value == 28.1
    assert dp.metadata["resolved_symbol"] == "UUP"
    assert client.get_latest_bar.call_count == 2


@patch("macromind.crawlers.market_crawler.load_market_watchlist")
@patch("macromind.crawlers.market_crawler.YFinanceClient")
def test_fetch_returns_datapoints(mock_client_cls: MagicMock, mock_load: MagicMock) -> None:
    mock_load.return_value = [
        MarketTickerConfig(
            indicator="SPY",
            symbol="SPY",
            category="equity",
            unit="usd",
        ),
    ]
    mock_client_cls.return_value.get_latest_bar.return_value = LatestBar(
        observation_date=date(2026, 5, 29),
        close=500.0,
        metadata={"ticker": "SPY"},
    )
    crawler = MarketCrawler()
    with patch("macromind.crawlers.market_crawler.time.sleep"):
        points = crawler.fetch({})
    assert len(points) == 1
    assert points[0].indicator == "SPY"
