from __future__ import annotations

from macromind.brief.ranking import rank_top_deltas
from macromind.signals.delta import SignalDelta


def _delta(
    signal_name: str,
    *,
    label_changed: bool = False,
    value_delta: float | None = None,
    label: str | None = "a",
    prev_label: str | None = "b",
    value: float | None = 1.0,
    prev_value: float | None = 0.0,
) -> SignalDelta:
    return SignalDelta(
        signal_name=signal_name,
        status="computed",
        value=value,
        label=label,
        prev_value=prev_value,
        prev_label=prev_label,
        value_delta=value_delta,
        label_changed=label_changed,
        comparable=True,
    )


def test_rank_top_deltas_label_beats_value() -> None:
    deltas = [
        _delta("growth_regime", value_delta=0.5),
        _delta("risk_regime", label_changed=True, value_delta=0.1),
    ]
    top = rank_top_deltas(deltas, n=3)
    assert [d.signal_name for d in top] == ["risk_regime", "growth_regime"]


def test_rank_top_deltas_excludes_market_state() -> None:
    deltas = [
        _delta("market_state", label_changed=True),
        _delta("risk_regime", value_delta=0.01),
    ]
    top = rank_top_deltas(deltas, n=3)
    assert len(top) == 1
    assert top[0].signal_name == "risk_regime"


def test_rank_top_deltas_tie_break_by_name() -> None:
    deltas = [
        _delta("growth_regime", value_delta=0.2),
        _delta("risk_regime", value_delta=0.2),
    ]
    top = rank_top_deltas(deltas, n=3)
    assert [d.signal_name for d in top] == ["growth_regime", "risk_regime"]


def test_rank_top_deltas_fewer_than_three_changes() -> None:
    deltas = [
        _delta("risk_regime", value_delta=0.1),
        _delta("growth_regime", value_delta=0.0),
        _delta("market_state", label_changed=True),
    ]
    top = rank_top_deltas(deltas, n=3)
    assert len(top) == 1
    assert top[0].signal_name == "risk_regime"


def test_rank_top_deltas_no_material_changes() -> None:
    deltas = [
        _delta("risk_regime", value_delta=0.0),
        _delta("growth_regime", label_changed=False, value_delta=None),
    ]
    assert rank_top_deltas(deltas, n=3) == []
