import type { SignalDelta } from '../types/desk'

/** Composite + overlay signals — not shown in desk/brief change lists */
export const EXCLUDED_CHANGE_SIGNALS = new Set([
  'market_state',
  'fed_rate_context',
  'inflation_pm_overlay',
])

export function hasMaterialChange(delta: SignalDelta): boolean {
  if (delta.label_changed) return true
  if (delta.value_delta != null && delta.value_delta !== 0) return true
  return false
}

function sortKey(delta: SignalDelta): [number, number, string] {
  const absDelta = delta.value_delta != null ? Math.abs(delta.value_delta) : 0
  return [-Number(delta.label_changed), -absDelta, delta.signal_name]
}

export function sortDeltas(deltas: SignalDelta[]): SignalDelta[] {
  return [...deltas].sort((a, b) => {
    const [aLabel, aDelta, aName] = sortKey(a)
    const [bLabel, bDelta, bName] = sortKey(b)
    if (aLabel !== bLabel) return aLabel - bLabel
    if (aDelta !== bDelta) return aDelta - bDelta
    return aName.localeCompare(bName)
  })
}

function filterMaterialRegimeDeltas(deltas: SignalDelta[]): SignalDelta[] {
  return deltas.filter(
    (delta) =>
      !EXCLUDED_CHANGE_SIGNALS.has(delta.signal_name) && hasMaterialChange(delta),
  )
}

/** Brief: top N material regime changes */
export function rankTopDeltas(deltas: SignalDelta[], n = 3): SignalDelta[] {
  return sortDeltas(filterMaterialRegimeDeltas(deltas)).slice(0, n)
}

/** Desk: all material regime changes, sorted by importance */
export function filterDeskDeltas(deltas: SignalDelta[]): SignalDelta[] {
  return sortDeltas(filterMaterialRegimeDeltas(deltas))
}
