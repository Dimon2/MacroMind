from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from macromind.db.signal_snapshot import SignalSnapshotRow
from macromind.signals.delta import build_deltas, build_deltas_for_date, compute_signal_deltas

_NOW = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)
_DAY = date(2026, 6, 2)
_PREV = date(2026, 6, 1)


def _row(
    signal_name: str,
    *,
    status: str = "computed",
    value: float | None = 1.0,
    label: str | None = "risk_on",
    snapshot_date: date = _DAY,
) -> SignalSnapshotRow:
    return SignalSnapshotRow(
        snapshot_date=snapshot_date,
        signal_name=signal_name,
        status=status,
        value=value,
        label=label,
        reason=None,
        inputs={},
        metadata={},
        as_of=_NOW,
    )


def test_compute_signal_deltas_value_and_label() -> None:
    current = [_row("risk_regime", value=2.0, label="risk_on")]
    previous = [_row("risk_regime", value=1.0, label="neutral", snapshot_date=_PREV)]
    deltas = compute_signal_deltas(current, previous)
    assert len(deltas) == 1
    assert deltas[0].value_delta == 1.0
    assert deltas[0].label_changed is True
    assert deltas[0].comparable is True


def test_compute_signal_deltas_skipped_not_comparable() -> None:
    current = [_row("risk_regime", status="skipped", value=None, label=None)]
    previous = [_row("risk_regime", snapshot_date=_PREV)]
    deltas = compute_signal_deltas(current, previous)
    assert deltas[0].value_delta is None
    assert deltas[0].comparable is False


def test_compute_signal_deltas_no_previous() -> None:
    deltas = compute_signal_deltas([_row("risk_regime")], [])
    assert deltas[0].prev_value is None
    assert deltas[0].comparable is False


def test_build_deltas_no_baseline() -> None:
    repo = MagicMock()
    current = [_row("risk_regime")]
    repo.load_previous_date.return_value = None

    prev_date, deltas = build_deltas(current, repo)

    assert prev_date is None
    assert len(deltas) == 1
    assert deltas[0].prev_value is None
    repo.load_for_date.assert_not_called()


def test_build_deltas_reuses_current_rows() -> None:
    repo = MagicMock()
    current = [_row("risk_regime", value=2.0)]
    repo.load_previous_date.return_value = _PREV
    repo.load_for_date.return_value = [_row("risk_regime", value=1.0, snapshot_date=_PREV)]

    prev_date, deltas = build_deltas(current, repo)

    assert prev_date == _PREV
    assert deltas[0].value_delta == 1.0
    repo.load_for_date.assert_called_once_with(_PREV)


def test_build_deltas_for_date_with_baseline() -> None:
    current = [_row("market_state", label="risk_on_easy_stable_expanding")]
    previous = [
        _row(
            "market_state",
            label="risk_off_tight_rising_contracting",
            snapshot_date=_PREV,
        )
    ]
    deltas = compute_signal_deltas(current, previous)
    assert deltas[0].label_changed is True
    assert deltas[0].comparable is True


def test_compute_signal_deltas_market_state_label() -> None:
    repo = MagicMock()
    repo.load_for_date.side_effect = lambda d: (
        [_row("risk_regime", value=2.0)]
        if d == _DAY
        else [_row("risk_regime", value=1.0, snapshot_date=_PREV)]
    )
    repo.load_previous_date.return_value = _PREV
    prev_date, deltas = build_deltas_for_date(_DAY, repo)
    assert prev_date == _PREV
    assert deltas[0].value_delta == 1.0
