import type { SignalDelta } from '../types/desk'

function formatNum(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2)
}

function formatDelta(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${formatNum(value)}`
}

export function formatDeltaLine(delta: SignalDelta): string {
  const parts: string[] = []

  if (delta.label_changed && delta.prev_label != null && delta.label != null) {
    parts.push(`${delta.signal_name} — ${delta.prev_label} → ${delta.label}`)
  } else if (delta.label_changed) {
    parts.push(`${delta.signal_name} — label changed`)
  }

  if (
    delta.value_delta != null &&
    delta.prev_value != null &&
    delta.value != null
  ) {
    const valuePart = `${delta.signal_name} — ${formatNum(delta.prev_value)} → ${formatNum(delta.value)}`
    if (parts.length > 0) {
      return `${parts[0]} (Δ ${formatDelta(delta.value_delta)})`
    }
    parts.push(valuePart)
  }

  if (parts.length === 0) {
    return `${delta.signal_name} — changed`
  }

  return parts[0]
}

export function formatDeltaValue(delta: SignalDelta): string | null {
  if (delta.value_delta == null) return null
  return `Δ ${formatDelta(delta.value_delta)}`
}

export function deltaDirection(delta: SignalDelta): 'up' | 'down' | 'flat' {
  if (delta.value_delta == null || delta.value_delta === 0) return 'flat'
  return delta.value_delta > 0 ? 'up' : 'down'
}
