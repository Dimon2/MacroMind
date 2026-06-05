from __future__ import annotations

from datetime import date, datetime, timezone

from macromind.brief.context import BriefContext
from macromind.brief.renderer import render_brief
from macromind.db.signal_snapshot import SignalSnapshotRow
from macromind.signals.delta import SignalDelta

_NOW = datetime(2026, 6, 5, 14, 0, tzinfo=timezone.utc)
_DAY = date(2026, 6, 5)
_PREV = date(2026, 6, 4)


def _row(
    signal_name: str,
    *,
    status: str = "computed",
    value: float | None = None,
    label: str | None = None,
    reason: str | None = None,
    inputs: dict | None = None,
    metadata: dict | None = None,
) -> SignalSnapshotRow:
    return SignalSnapshotRow(
        snapshot_date=_DAY,
        signal_name=signal_name,
        status=status,
        value=value,
        label=label,
        reason=reason,
        inputs=inputs or {},
        metadata=metadata or {},
        as_of=_NOW,
    )


def _full_context() -> BriefContext:
    snapshots = {
        "risk_regime": _row("risk_regime", value=1.0, label="risk_on"),
        "liquidity_regime": _row("liquidity_regime", value=0.0, label="easy"),
        "inflation_regime": _row("inflation_regime", value=3.0, label="stable"),
        "growth_regime": _row("growth_regime", value=2.0, label="expanding"),
        "market_state": _row(
            "market_state",
            label="risk_on_easy_stable_expanding",
            metadata={"label": "risk_on_easy_stable_expanding"},
        ),
        "rates_curve_proxy": _row(
            "rates_curve_proxy",
            value=0.25,
            label="normal",
            metadata={"curve_state": "normal"},
        ),
        "macro_implied_inflation_prob": _row(
            "macro_implied_inflation_prob",
            value=0.58,
            inputs={"markets_count": 2},
        ),
    }
    deltas = [
        SignalDelta(
            signal_name="risk_regime",
            status="computed",
            value=1.0,
            label="risk_on",
            prev_value=0.0,
            prev_label="neutral",
            value_delta=1.0,
            label_changed=True,
            comparable=True,
        ),
        SignalDelta(
            signal_name="macro_implied_inflation_prob",
            status="computed",
            value=0.58,
            label=None,
            prev_value=0.54,
            prev_label=None,
            value_delta=0.04,
            label_changed=False,
            comparable=True,
        ),
    ]
    crawl_status = {
        "as_of": _NOW.isoformat(),
        "crawlers": {
            "fred": {
                "last_success": {
                    "finished_at": "2026-06-05T12:00:00+00:00",
                    "rows_persisted": 10,
                    "age_hours": 2.0,
                },
                "last_run": {"status": "success"},
            },
            "kalshi": {
                "last_success": {
                    "finished_at": "2026-06-05T11:00:00+00:00",
                    "rows_persisted": 5,
                    "age_hours": 3.0,
                },
                "last_run": {"status": "success"},
            },
            "market": {
                "last_success": {
                    "finished_at": "2026-06-05T10:00:00+00:00",
                    "rows_persisted": 8,
                    "age_hours": 4.0,
                },
                "last_run": {"status": "success"},
            },
        },
        "missing": [],
    }
    return BriefContext(
        snapshot_date=_DAY,
        previous_snapshot_date=_PREV,
        as_of=_NOW,
        snapshots_by_name=snapshots,
        deltas=deltas,
        crawl_status=crawl_status,
    )


def test_render_brief_full_snapshot() -> None:
    text = render_brief(_full_context())
    assert "# MacroMind Daily Brief — 2026-06-05" in text
    assert "**Signals as of:** 2026-06-05T14:00:00+00:00" in text
    assert "**Previous snapshot:** 2026-06-04" in text
    assert "| fred | 2026-06-05T12:00:00+00:00 | 2.0 | ok |" in text
    assert "**Composite:** risk_on_easy_stable_expanding" in text
    assert "**Risk:** risk_on · **Liquidity:** easy · **Inflation:** stable · **Growth:** expanding" in text
    assert "1. risk_regime: neutral → risk_on; 0 → 1 (Δ +1)" in text
    assert "2. macro_implied_inflation_prob: 0.54 → 0.58 (Δ +0.04)" in text
    assert "**Curve (rates_curve_proxy):** normal (spread 0.25)" in text
    assert "**PM inflation prob:** 58.0% (2 markets)" in text


def test_render_brief_partial_dimensions() -> None:
    snapshots = {
        "risk_regime": _row("risk_regime", value=1.0, label="risk_on"),
        "market_state": _row(
            "market_state",
            status="skipped",
            reason="missing_dimension_labels",
            label=None,
        ),
    }
    ctx = BriefContext(
        snapshot_date=_DAY,
        previous_snapshot_date=None,
        as_of=_NOW,
        snapshots_by_name=snapshots,
        deltas=[],
        crawl_status={"crawlers": {}, "missing": ["fred", "kalshi", "market"]},
    )
    text = render_brief(ctx)
    assert "**Composite:** — (missing_dimension_labels)" in text
    assert "**Risk:** risk_on · **Liquidity:** — · **Inflation:** — · **Growth:** —" in text


def test_render_brief_skipped_overlays() -> None:
    snapshots = {
        "rates_curve_proxy": _row(
            "rates_curve_proxy",
            status="skipped",
            reason="missing_required_inputs",
        ),
        "macro_implied_inflation_prob": _row(
            "macro_implied_inflation_prob",
            status="skipped",
            reason="missing_required_inputs",
        ),
    }
    ctx = BriefContext(
        snapshot_date=_DAY,
        previous_snapshot_date=None,
        as_of=_NOW,
        snapshots_by_name=snapshots,
        deltas=[],
        crawl_status={"crawlers": {}, "missing": []},
    )
    text = render_brief(ctx)
    assert "**Curve (rates_curve_proxy):** — (missing_required_inputs)" in text
    assert "**PM inflation prob:** — (missing_required_inputs)" in text


def test_render_brief_no_material_changes() -> None:
    ctx = BriefContext(
        snapshot_date=_DAY,
        previous_snapshot_date=_PREV,
        as_of=_NOW,
        snapshots_by_name={},
        deltas=[
            SignalDelta(
                signal_name="risk_regime",
                status="computed",
                value=1.0,
                label="risk_on",
                prev_value=1.0,
                prev_label="risk_on",
                value_delta=0.0,
                label_changed=False,
                comparable=True,
            )
        ],
        crawl_status={"crawlers": {}, "missing": []},
    )
    text = render_brief(ctx)
    assert "No material changes vs previous snapshot." in text
