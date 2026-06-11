import type { DeskCards } from '../../types/desk'

type MarketStateTableProps = {
  cards: DeskCards
}

const ROWS: { key: keyof DeskCards; label: string }[] = [
  { key: 'risk', label: 'Risk' },
  { key: 'liquidity', label: 'Liquidity (level)' },
  { key: 'inflation', label: 'Inflation' },
  { key: 'growth', label: 'Growth' },
  { key: 'credit', label: 'Credit' },
]

function regimeLabel(cards: DeskCards, key: keyof DeskCards): string {
  if (key === 'liquidity') {
    const level = cards.liquidity.level.label ?? '—'
    const trend = cards.liquidity.trend.label
    return trend ? `${level} · trend ${trend}` : level
  }
  return cards[key].regime.label ?? '—'
}

export function MarketStateTable({ cards }: MarketStateTableProps) {
  return (
    <div className="divide-y divide-zinc-800 rounded-lg border border-zinc-800">
      {ROWS.map(({ key, label }) => (
        <div key={key} className="flex items-center justify-between px-4 py-3">
          <span className="text-sm text-zinc-400">{label}</span>
          <span className="font-mono text-sm text-zinc-200">
            {regimeLabel(cards, key)}
          </span>
        </div>
      ))}
    </div>
  )
}
