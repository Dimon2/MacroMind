import { getCompositePills, pillStyle } from '../../lib/composite'
import type { DeskCards } from '../../types/desk'

type CompositePillsProps = {
  cards: DeskCards
}

export function CompositePills({ cards }: CompositePillsProps) {
  const pills = getCompositePills(cards)

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3">
      <p className="text-xs text-zinc-500">Composite:</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {pills.map((pill) => (
          <span
            key={pill.key}
            className={`inline-flex rounded-full border px-2.5 py-0.5 font-mono text-xs ${pillStyle(pill.key)}`}
          >
            {pill.label ?? '—'}
          </span>
        ))}
      </div>
    </div>
  )
}
