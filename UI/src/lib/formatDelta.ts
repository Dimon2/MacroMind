import type { SignalDelta } from '../types/desk'

const SIGNAL_NAMES: Record<string, string> = {
  risk_regime: 'Risk',
  liquidity_trend_regime: 'Liquidity trend',
  liquidity_level_regime: 'Liquidity level',
  inflation_regime: 'Inflation',
  growth_regime: 'Growth',
  credit_regime: 'Credit',
}

type ValueKind = 'cpi_yoy' | 'hy_spread' | 'score'

const VALUE_KIND: Record<string, ValueKind> = {
  inflation_regime: 'cpi_yoy',
  credit_regime: 'hy_spread',
  risk_regime: 'score',
  liquidity_trend_regime: 'score',
  liquidity_level_regime: 'score',
  growth_regime: 'score',
}

const METRIC_LABEL: Record<string, string> = {
  inflation_regime: 'CPI YoY',
  credit_regime: 'HY OAS spread',
  risk_regime: 'Regime score',
  liquidity_trend_regime: 'Regime score',
  liquidity_level_regime: 'Regime score',
  growth_regime: 'Regime score',
}

export function signalDisplayName(signalName: string): string {
  return SIGNAL_NAMES[signalName] ?? signalName
}

function formatNum(value: number): string {
  const rounded = Math.round(value * 100) / 100
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(2)
}

function formatSignedDelta(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${formatNum(value)}`
}

function valueKind(signalName: string): ValueKind {
  return VALUE_KIND[signalName] ?? 'score'
}

function formatValue(value: number, kind: ValueKind): string {
  if (kind === 'cpi_yoy' || kind === 'hy_spread') return `${formatNum(value)}%`
  return formatNum(value)
}

function formatDeltaWithUnit(delta: number, kind: ValueKind): string {
  const signed = formatSignedDelta(delta)
  if (kind === 'cpi_yoy') return `Δ ${signed} pp`
  if (kind === 'hy_spread') return `Δ ${signed}% spread`
  return `Δ ${signed} score`
}

/** Label transition, e.g. "stable → rising" */
export function formatLabelChange(delta: SignalDelta): string | null {
  if (!delta.label_changed) return null
  const prev = delta.prev_label ?? '—'
  const next = delta.label ?? '—'
  return `${prev} → ${next}`
}

/** Underlying metric movement, e.g. "CPI YoY 2.8% → 3.3%" */
export function formatMetricChange(delta: SignalDelta): string | null {
  if (delta.prev_value == null || delta.value == null) return null
  const kind = valueKind(delta.signal_name)
  const label = METRIC_LABEL[delta.signal_name] ?? 'Value'
  return `${label} ${formatValue(delta.prev_value, kind)} → ${formatValue(delta.value, kind)}`
}

/** One-line summary for Brief */
export function formatDeltaLine(delta: SignalDelta): string {
  const name = signalDisplayName(delta.signal_name)
  const labelPart = formatLabelChange(delta)
  const metricPart = formatMetricChange(delta)
  const kind = valueKind(delta.signal_name)

  if (labelPart && metricPart && delta.value_delta != null && delta.value_delta !== 0) {
    return `${name} — ${labelPart}; ${metricPart}`
  }
  if (labelPart) return `${name} — ${labelPart}`
  if (metricPart && delta.value_delta != null) {
    return `${name} — ${metricPart} (${formatDeltaWithUnit(delta.value_delta, kind)})`
  }
  return `${name} — changed`
}

export function formatDeltaValue(delta: SignalDelta): string | null {
  if (delta.value_delta == null || delta.value_delta === 0) return null
  return formatDeltaWithUnit(delta.value_delta, valueKind(delta.signal_name))
}

export function deltaDirection(delta: SignalDelta): 'up' | 'down' | 'flat' {
  if (delta.value_delta == null || delta.value_delta === 0) return 'flat'
  return delta.value_delta > 0 ? 'up' : 'down'
}
