import type { DeskOverlays } from '../types/desk'

export type PmMarketRow = {
  market_ticker?: string
  outcome_label?: string
  yes_probability?: number
  event_ticker?: string
  url?: string
  strike?: number
  strike_op?: string
  unit_hint?: string
}

const STRIKE_OP_LABELS: Record<string, string> = {
  above: 'above',
  below: 'below',
  at_least: 'at least',
}

function asPmMarket(row: Record<string, unknown>): PmMarketRow {
  return row as PmMarketRow
}

function formatPct(probability: number): string {
  return `${Math.round(probability * 100)}%`
}

function formatStrikeValue(strike: number, unitHint?: string): string {
  if (unitHint === 'percent') return `${strike}%`
  if (unitHint === 'bps') return `${strike} bps`
  if (unitHint === 'count') return strike.toLocaleString()
  return String(strike)
}

function metricFromEvent(eventTicker?: string): string | null {
  if (!eventTicker) return null
  if (eventTicker.startsWith('KXCPI')) return 'CPI YoY'
  if (eventTicker.startsWith('KXFED')) return 'Fed funds target'
  if (eventTicker.startsWith('KXGDP')) return 'US GDP growth'
  if (eventTicker.startsWith('KXU3') || eventTicker.startsWith('KXUSNFP')) return 'Employment'
  return null
}

/** e.g. "above 3.0%" — direction + level in one phrase */
export function formatThresholdPhrase(market: PmMarketRow): string | null {
  if (market.strike == null || !market.strike_op) return null
  const op = STRIKE_OP_LABELS[market.strike_op] ?? market.strike_op.replace(/_/g, ' ')
  return `${op} ${formatStrikeValue(market.strike, market.unit_hint)}`
}

function periodFromEventTicker(eventTicker?: string): string | null {
  if (!eventTicker) return null
  // KXCPIYOY-26JUN → June 2026
  const match = eventTicker.match(/-(\d{2})([A-Z]{3})$/)
  if (!match) return null
  const year = `20${match[1]}`
  const monthMap: Record<string, string> = {
    JAN: 'January',
    FEB: 'February',
    MAR: 'March',
    APR: 'April',
    MAY: 'May',
    JUN: 'June',
    JUL: 'July',
    AUG: 'August',
    SEP: 'September',
    OCT: 'October',
    NOV: 'November',
    DEC: 'December',
  }
  const month = monthMap[match[2]]
  return month ? `${month} ${year}` : null
}

/** Main readable sentence: "40% chance CPI YoY is above 3.0%" */
export function pmMarketClaim(market: PmMarketRow): string {
  const threshold = formatThresholdPhrase(market)
  const metric = metricFromEvent(market.event_ticker) ?? 'Inflation'
  const period = periodFromEventTicker(market.event_ticker)

  if (market.yes_probability != null && threshold) {
    const base = `${formatPct(market.yes_probability)} chance ${metric} is ${threshold}`
    return period ? `${base} in ${period}` : base
  }

  if (market.outcome_label && market.yes_probability != null) {
    return `${formatPct(market.yes_probability)} chance: ${market.outcome_label}`
  }

  if (market.outcome_label) return market.outcome_label
  if (market.market_ticker) return market.market_ticker
  return 'Kalshi inflation market'
}

/** Secondary line: source only, no jargon */
export function pmMarketSource(market: PmMarketRow): string {
  const parts: string[] = ['Kalshi']
  if (market.market_ticker) parts.push(market.market_ticker)
  return parts.join(' · ')
}

export function primaryInflationPmMarket(overlays: DeskOverlays): PmMarketRow | null {
  const raw = overlays.inflation_pm.markets[0]
  if (!raw) return null
  return asPmMarket(raw)
}

export function inflationPmDisplay(overlays: DeskOverlays): {
  pct: string | null
  claim: string
  source: string
  threshold: string | null
} | null {
  if (overlays.inflation_pm.status !== 'computed') return null
  const market = primaryInflationPmMarket(overlays)
  if (!market || market.yes_probability == null) return null
  return {
    pct: formatPct(market.yes_probability),
    claim: pmMarketClaim(market),
    source: pmMarketSource(market),
    threshold: formatThresholdPhrase(market),
  }
}

export function formatPmMarketLine(market: PmMarketRow): {
  claim: string
  probability: string | null
  source: string
} {
  return {
    claim: pmMarketClaim(market),
    probability: market.yes_probability != null ? formatPct(market.yes_probability) : null,
    source: pmMarketSource(market),
  }
}

export function inflationPmMarkets(overlays: DeskOverlays): PmMarketRow[] {
  return overlays.inflation_pm.markets.map(asPmMarket)
}

export function fedKalshiMarkets(overlays: DeskOverlays): PmMarketRow[] {
  return overlays.fed_compare.kalshi_markets.map(asPmMarket)
}
