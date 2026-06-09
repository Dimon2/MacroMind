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
        "liquidity_regime": _row(
            "liquidity_regime",
            value=2.0,
            label="easy",
            inputs={
                "net_liquidity": 7_000_000.0,
                "net_liquidity_change_wow_pct": 0.3,
                "net_liquidity_date": "2026-06-05",
                "M2SL_change_mom_pct": 0.42,
                "M2SL_yoy_pct": 1.8,
                "M2SL_yoy_status": "computed",
            },
        ),
        "inflation_regime": _row("inflation_regime", value=3.0, label="stable"),
        "growth_regime": _row(
            "growth_regime",
            value=2.0,
            label="expanding",
            inputs={"curve_spread": 0.25, "curve_state": "normal", "curve_source": "T10Y2Y"},
        ),
        "credit_regime": _row("credit_regime", value=4.0, label="normal"),
        "market_state": _row(
            "market_state",
            label="risk_on_easy_stable_expanding_normal",
            metadata={"label": "risk_on_easy_stable_expanding_normal"},
        ),
        "inflation_pm_overlay": _row(
            "inflation_pm_overlay",
            value=None,
            inputs={
                "markets": [
                    {"outcome_label": "Above 3%", "yes_probability": 0.41},
                    {"outcome_label": "Above 4%", "yes_probability": 0.12},
                ]
            },
        ),
        "fed_rate_context": _row(
            "fed_rate_context",
            value=None,
            inputs={
                "effective_rate": 4.25,
                "kalshi_markets": [{"outcome_label": "Cut 25bp by Sep", "yes_probability": 0.68}],
            },
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
            signal_name="credit_regime",
            status="computed",
            value=4.0,
            label="normal",
            prev_value=3.8,
            prev_label="relaxed",
            value_delta=0.2,
            label_changed=True,
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
    assert "**Composite:** risk_on_easy_stable_expanding_normal" in text
    assert "**Credit:** normal" in text
    assert "**Net liquidity:**" in text
    assert "**M2 MoM:**" in text
    assert "**M2 YoY:**" in text
    assert "1. risk_regime: neutral → risk_on" in text
    assert "**Curve (growth):** normal (spread 0.25)" in text
    assert "**PM inflation:** Above 3%: 41.0%" in text
    assert "**Fed compare:** effective 4.25%" in text


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
    assert "**Credit:** —" in text


def test_render_brief_skipped_overlays() -> None:
    snapshots = {
        "growth_regime": _row(
            "growth_regime",
            status="skipped",
            reason="insufficient_history",
        ),
        "inflation_pm_overlay": _row(
            "inflation_pm_overlay",
            status="skipped",
            reason="missing_required_inputs",
        ),
        "fed_rate_context": _row(
            "fed_rate_context",
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
    assert "**Curve (growth):** — (insufficient_history)" in text
    assert "**PM inflation:** — (missing_required_inputs)" in text
    assert "**Fed compare:** — (missing_required_inputs)" in text


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
