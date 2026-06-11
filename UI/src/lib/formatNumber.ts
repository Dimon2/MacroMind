export function formatPct(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(digits)}%`
}

export function formatNum(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return '—'
  return value.toFixed(digits)
}
