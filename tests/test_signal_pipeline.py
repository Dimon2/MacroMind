from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from macromind.models import DataPoint
from macromind.signals.pipeline import macro_datapoints_for_signals, merge_macro_datapoints


def _dp(
    indicator: str,
    period: str,
    *,
    source: str = "fred",
    value: float = 1.0,
    fetched_at: datetime | None = None,
) -> DataPoint:
    return DataPoint(
        source=source,
        indicator=indicator,
        value=value,
        unit="index",
        period=period,
        fetched_at=fetched_at or datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc),
        metadata={"category": "inflation"},
    )


def test_merge_macro_datapoints_dedupes_same_period() -> None:
    older = _dp("CPIAUCSL", "2026-04-01", fetched_at=datetime(2026, 6, 1, tzinfo=timezone.utc))
    newer = _dp("CPIAUCSL", "2026-04-01", value=310.0)
    merged = merge_macro_datapoints([older], [newer])
    assert len(merged) == 1
    assert merged[0].value == 310.0


def test_merge_macro_datapoints_keeps_distinct_periods() -> None:
    latest = [_dp("CPIAUCSL", "2026-04-01")]
    history = [_dp("CPIAUCSL", "2026-03-01", value=308.0)]
    merged = merge_macro_datapoints(latest, history)
    assert len(merged) == 2
    periods = {dp.period for dp in merged}
    assert periods == {"2026-04-01", "2026-03-01"}


def test_macro_datapoints_for_signals_loads_latest_and_regime_history() -> None:
    macro = MagicMock()
    macro.load_latest_datapoints.return_value = [_dp("DGS10", "2026-06-01", value=4.2)]
    macro.load_observations.return_value = [
        _dp("CPIAUCSL", "2026-04-01"),
        _dp("CPIAUCSL", "2026-03-01", value=308.0),
    ]

    result = macro_datapoints_for_signals(macro)

    macro.load_observations.assert_called_once()
    call = macro.load_observations.call_args
    assert call[0][0] == "fred"
    assert "CPIAUCSL" in call[0][1]
    assert call[1]["last_n"] == 60
    assert len(result) == 3
    assert {dp.indicator for dp in result} == {"DGS10", "CPIAUCSL"}
