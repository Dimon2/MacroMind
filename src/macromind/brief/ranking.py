from __future__ import annotations

from macromind.signals.delta import SignalDelta

_EXCLUDED_SIGNALS = frozenset({"market_state"})


def _has_material_change(delta: SignalDelta) -> bool:
    if delta.label_changed:
        return True
    if delta.value_delta is not None and delta.value_delta != 0:
        return True
    return False


def _sort_key(delta: SignalDelta) -> tuple[int, float, str]:
    abs_delta = abs(delta.value_delta) if delta.value_delta is not None else 0.0
    return (-int(delta.label_changed), -abs_delta, delta.signal_name)


def rank_top_deltas(deltas: list[SignalDelta], n: int = 3) -> list[SignalDelta]:
    pool = [
        delta
        for delta in deltas
        if delta.signal_name not in _EXCLUDED_SIGNALS and _has_material_change(delta)
    ]
    pool.sort(key=_sort_key)
    return pool[:n]
