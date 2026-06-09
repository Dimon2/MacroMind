import type { SignalDelta } from '../types/desk'

const EXCLUDED_SIGNALS = new Set(['market_state'])

function hasMaterialChange(delta: SignalDelta): boolean {
  if (delta.label_changed) return true
  if (delta.value_delta != null && delta.value_delta !== 0) return true
  return false
}

function sortKey(delta: SignalDelta): [number, number, string] {
  const absDelta = delta.value_delta != null ? Math.abs(delta.value_delta) : 0
  return [-Number(delta.label_changed), -absDelta, delta.signal_name]
}

export function rankTopDeltas(deltas: SignalDelta[], n = 3): SignalDelta[] {
  const pool = deltas.filter(
    (delta) => !EXCLUDED_SIGNALS.has(delta.signal_name) && hasMaterialChange(delta),
  )
  pool.sort((a, b) => {
    const [aLabel, aDelta, aName] = sortKey(a)
    const [bLabel, bDelta, bName] = sortKey(b)
    if (aLabel !== bLabel) return aLabel - bLabel
    if (aDelta !== bDelta) return aDelta - bDelta
    return aName.localeCompare(bName)
  })
  return pool.slice(0, n)
}
