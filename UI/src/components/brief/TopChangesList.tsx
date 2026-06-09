import { deltaDirection, formatDeltaLine, formatDeltaValue } from '../../lib/formatDelta'
import type { SignalDelta } from '../../types/desk'

type TopChangesListProps = {
  deltas: SignalDelta[]
}

function DirectionIcon({ direction }: { direction: 'up' | 'down' | 'flat' }) {
  if (direction === 'up') {
    return <span className="text-emerald-400" aria-hidden>▲</span>
  }
  if (direction === 'down') {
    return <span className="text-red-400" aria-hidden>▼</span>
  }
  return null
}

export function TopChangesList({ deltas }: TopChangesListProps) {
  if (deltas.length === 0) {
    return (
      <p className="text-sm text-zinc-500">No material changes vs previous snapshot.</p>
    )
  }

  return (
    <ol className="divide-y divide-zinc-800 rounded-lg border border-zinc-800">
      {deltas.map((delta, index) => {
        const direction = deltaDirection(delta)
        const deltaText = formatDeltaValue(delta)
        const colorClass =
          direction === 'up'
            ? 'text-emerald-400'
            : direction === 'down'
              ? 'text-red-400'
              : 'text-zinc-400'

        return (
          <li key={delta.signal_name} className="flex items-center gap-3 px-4 py-3">
            <span className="w-5 shrink-0 text-sm text-zinc-500">{index + 1}</span>
            <p className="min-w-0 flex-1 text-sm text-zinc-300">{formatDeltaLine(delta)}</p>
            {deltaText && (
              <div className={`flex shrink-0 items-center gap-1 font-mono text-sm ${colorClass}`}>
                <DirectionIcon direction={direction} />
                <span>{deltaText}</span>
              </div>
            )}
          </li>
        )
      })}
    </ol>
  )
}
