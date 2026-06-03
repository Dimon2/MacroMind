from macromind.macro.fred_watchlist import FredSeriesConfig, load_fred_watchlist


def test_fetch_limit_for_count_bootstrap() -> None:
    cfg = FredSeriesConfig(
        series_id="CPIAUCSL",
        category="inflation",
        unit="index",
        min_points=13,
        bootstrap_limit=15,
        steady_limit=5,
    )
    assert cfg.fetch_limit_for_count(0) == 15
    assert cfg.fetch_limit_for_count(12) == 15
    assert cfg.fetch_limit_for_count(13) == 5
    assert cfg.fetch_limit_for_count(20) == 5


def test_load_fred_watchlist_cpi_min_points() -> None:
    configs = load_fred_watchlist()
    by_id = {c.series_id: c for c in configs}
    assert by_id["CPIAUCSL"].min_points == 13
    assert by_id["DGS10"].min_points == 1
    assert by_id["WALCL"].min_points == 2
