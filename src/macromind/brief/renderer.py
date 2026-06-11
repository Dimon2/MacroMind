from __future__ import annotations

from macromind.brief.context import BriefContext, PERSIST_CRAWLERS
from macromind.brief.ranking import rank_top_deltas
from macromind.db.signal_snapshot import SignalSnapshotRow
from macromind.signals.delta import SignalDelta


def render_brief(ctx: BriefContext) -> str:
    lines = [
        f"# MacroMind Daily Brief — {ctx.snapshot_date.isoformat()}",
        "",
        f"**Signals as of:** {ctx.as_of.isoformat()}  ",
        f"**Previous snapshot:** {_format_previous_date(ctx.previous_snapshot_date)}",
        "",
        "## Data freshness",
        _render_freshness_table(ctx),
        "",
        "## Market state",
        _render_market_state(ctx),
        "",
        "## Liquidity",
        _render_liquidity_detail(ctx),
        "",
        "## What changed (top 3)",
        _render_top_deltas(ctx),
        "",
        "## Overlays",
        _render_overlays(ctx),
    ]
    return "\n".join(lines)


def _format_previous_date(previous: object | None) -> str:
    if previous is None:
        return "none"
    return str(previous)


def _render_freshness_table(ctx: BriefContext) -> str:
    header = "| Crawler | Last success (UTC) | Age (h) | Status |"
    separator = "| --- | --- | --- | --- |"
    rows = [header, separator]
    crawlers = ctx.crawl_status.get("crawlers") or {}

    for name in PERSIST_CRAWLERS:
        entry = crawlers.get(name) or {}
        last_success = entry.get("last_success")
        last_run = entry.get("last_run")

        if last_success is not None:
            finished_at = last_success.get("finished_at", "—")
            age_hours = last_success.get("age_hours", "—")
            status = "ok" if last_run and last_run.get("status") == "success" else "stale"
        elif last_run is not None:
            finished_at = "—"
            age_hours = "—"
            status = last_run.get("status", "unknown")
        else:
            finished_at = "—"
            age_hours = "—"
            status = "missing"

        rows.append(f"| {name} | {finished_at} | {age_hours} | {status} |")

    return "\n".join(rows)


def _render_market_state(ctx: BriefContext) -> str:
    market = ctx.snapshot("market_state")
    dimensions = ctx.dimension_labels()

    if market is not None and market.status == "computed" and market.label:
        composite = market.label
    elif market is not None and market.status == "skipped":
        reason = market.reason or "unknown"
        composite = f"— ({reason})"
    else:
        composite = "—"

    risk = dimensions.get("risk_regime") or "—"
    liquidity_level = dimensions.get("liquidity_level_regime") or "—"
    liquidity_trend_row = ctx.snapshot("liquidity_trend_regime")
    liquidity_trend = (
        liquidity_trend_row.label
        if liquidity_trend_row and liquidity_trend_row.status == "computed"
        else "—"
    )
    inflation = dimensions.get("inflation_regime") or "—"
    growth = dimensions.get("growth_regime") or "—"
    credit = dimensions.get("credit_regime") or "—"

    return (
        f"**Composite:** {composite}  \n"
        f"**Risk:** {risk} · **Liquidity (level):** {liquidity_level} · "
        f"**Trend:** {liquidity_trend} · "
        f"**Inflation:** {inflation} · **Growth:** {growth} · **Credit:** {credit}"
    )


def _render_liquidity_detail(ctx: BriefContext) -> str:
    level_row = ctx.snapshot("liquidity_level_regime")
    trend_row = ctx.snapshot("liquidity_trend_regime")
    context_row = ctx.snapshot("liquidity_context")

    if level_row is None and trend_row is None:
        return "— (missing)"

    lines: list[str] = []

    if level_row is not None and level_row.status == "computed":
        level_inputs = level_row.inputs or {}
        vs_52w = level_inputs.get("net_liquidity_vs_52w_pct")
        walcl_26w = level_inputs.get("WALCL_change_26w_pct")
        drain_26w = level_inputs.get("drain_change_26w_pct")
        lines.append(
            f"**Level:** {level_row.label} "
            f"(vs 52w avg {_format_delta_pct(_to_float(vs_52w))}, "
            f"WALCL 26w {_format_delta_pct(_to_float(walcl_26w))}, "
            f"drain 26w {_format_delta_pct(_to_float(drain_26w))})"
        )
    elif level_row is not None:
        lines.append(f"**Level:** — ({level_row.reason or 'skipped'})")

    if trend_row is not None and trend_row.status == "computed":
        trend_inputs = trend_row.inputs or {}
        net = trend_inputs.get("net_liquidity")
        net_chg = trend_inputs.get("net_liquidity_change_wow_pct")
        net_date = trend_inputs.get("net_liquidity_date", "—")
        lines.append(
            f"**Trend:** {trend_row.label} — net liq "
            f"{_format_num(net) if net is not None else '—'} M USD "
            f"(WoW {_format_delta_pct(_to_float(net_chg))}, as of {net_date})"
        )
    elif trend_row is not None:
        lines.append(f"**Trend:** — ({trend_row.reason or 'skipped'})")

    if context_row is not None and context_row.status == "computed":
        interpretation = (context_row.inputs or {}).get("interpretation")
        if interpretation:
            lines.append(f"**Context:** {interpretation}")

    mom = None
    yoy = None
    yoy_status = "—"
    if trend_row and trend_row.inputs:
        mom = trend_row.inputs.get("M2SL_change_mom_pct")
        yoy = trend_row.inputs.get("M2SL_yoy_pct")
        yoy_status = trend_row.inputs.get("M2SL_yoy_status", "—")
    elif level_row and level_row.inputs:
        mom = level_row.inputs.get("M2SL_change_mom_pct")
        yoy = level_row.inputs.get("M2SL_yoy_pct")
        yoy_status = level_row.inputs.get("M2SL_yoy_status", "—")

    if mom is not None:
        lines.append(f"**M2 MoM:** {_format_delta_pct(_to_float(mom))}")
    if yoy is not None:
        lines.append(f"**M2 YoY:** {_format_delta_pct(_to_float(yoy))}")
    elif yoy_status != "computed":
        lines.append(f"**M2 YoY:** — ({yoy_status})")

    return "  \n".join(lines) if lines else "— (missing)"


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _render_top_deltas(ctx: BriefContext) -> str:
    top = rank_top_deltas(ctx.deltas, n=3)
    if not top:
        return "No material changes vs previous snapshot."
    return "\n".join(f"{index}. {_format_delta_line(delta)}" for index, delta in enumerate(top, 1))


def _format_delta_line(delta: SignalDelta) -> str:
    parts: list[str] = []
    if delta.label_changed and delta.prev_label is not None and delta.label is not None:
        parts.append(f"{delta.signal_name}: {delta.prev_label} → {delta.label}")
    elif delta.label_changed:
        parts.append(f"{delta.signal_name}: label changed")

    if delta.value_delta is not None and delta.prev_value is not None and delta.value is not None:
        value_part = (
            f"{delta.signal_name}: {_format_num(delta.prev_value)} → "
            f"{_format_num(delta.value)} (Δ {_format_delta(delta.value_delta)})"
        )
        if parts:
            return f"{parts[0]}; {_format_num(delta.prev_value)} → {_format_num(delta.value)} (Δ {_format_delta(delta.value_delta)})"
        parts.append(value_part)

    if not parts:
        return f"{delta.signal_name}: changed"
    return parts[0]


def _format_num(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _format_delta(value: float) -> str:
    sign = "+" if value > 0 else ""
    if value == int(value):
        return f"{sign}{int(value)}"
    return f"{sign}{value:.4f}".rstrip("0").rstrip(".")


def _format_delta_pct(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def _render_overlays(ctx: BriefContext) -> str:
    growth_line = _render_growth_curve_overlay(ctx.snapshot("growth_regime"))
    pm_line = _render_inflation_pm_overlay(ctx.snapshot("inflation_pm_overlay"))
    fed_line = _render_fed_overlay(ctx.snapshot("fed_rate_context"))
    return f"- {growth_line}\n- {pm_line}\n- {fed_line}"


def _render_growth_curve_overlay(row: SignalSnapshotRow | None) -> str:
    if row is None or row.status != "computed":
        reason = row.reason if row is not None else "missing"
        return f"**Curve (growth):** — ({reason})"

    inputs = row.inputs or {}
    curve_state = inputs.get("curve_state", "—")
    spread = inputs.get("curve_spread")
    spread_str = _format_num(spread) if spread is not None else "—"
    return f"**Curve (growth):** {curve_state} (spread {spread_str})"


def _render_inflation_pm_overlay(row: SignalSnapshotRow | None) -> str:
    if row is None or row.status != "computed":
        reason = row.reason if row is not None else "missing"
        return f"**PM inflation:** — ({reason})"

    markets = row.inputs.get("markets") or []
    if not markets:
        return "**PM inflation:** — (no markets)"
    parts = []
    for market in markets[:5]:
        label = market.get("outcome_label") or market.get("market_ticker")
        prob = market.get("yes_probability")
        if prob is not None:
            parts.append(f"{label}: {prob * 100:.1f}%")
    return f"**PM inflation:** {', '.join(parts)}"


def _render_fed_overlay(row: SignalSnapshotRow | None) -> str:
    if row is None or row.status != "computed":
        reason = row.reason if row is not None else "missing"
        return f"**Fed compare:** — ({reason})"

    inputs = row.inputs or {}
    rate = inputs.get("effective_rate")
    rate_str = f"{rate}%" if rate is not None else "—"
    markets = inputs.get("kalshi_markets") or []
    if not markets:
        return f"**Fed compare:** effective {rate_str}"
    parts = []
    for market in markets[:5]:
        label = market.get("outcome_label") or market.get("market_ticker")
        prob = market.get("yes_probability")
        if prob is not None:
            parts.append(f"{label}: {prob * 100:.1f}%")
    return f"**Fed compare:** effective {rate_str}; Kalshi: {', '.join(parts)}"
