import type { DeskCards } from '../types/desk'

export type CompositePill = {
  key: 'risk' | 'liquidity' | 'inflation' | 'growth' | 'credit'
  label: string | null
}

const PILL_STYLES: Record<CompositePill['key'], string> = {
  risk: 'border-emerald-800/60 bg-emerald-950/40 text-emerald-300',
  liquidity: 'border-blue-800/60 bg-blue-950/40 text-blue-300',
  inflation: 'border-amber-800/60 bg-amber-950/40 text-amber-300',
  growth: 'border-emerald-800/60 bg-emerald-950/40 text-emerald-300',
  credit: 'border-purple-800/60 bg-purple-950/40 text-purple-300',
}

export function getCompositePills(cards: DeskCards): CompositePill[] {
  return [
    { key: 'risk', label: cards.risk.regime.label },
    { key: 'liquidity', label: cards.liquidity.regime.label },
    { key: 'inflation', label: cards.inflation.regime.label },
    { key: 'growth', label: cards.growth.regime.label },
    { key: 'credit', label: cards.credit.regime.label },
  ]
}

export function pillStyle(key: CompositePill['key']): string {
  return PILL_STYLES[key]
}
