import {
  deltaDirection,
  formatDeltaValue,
  formatLabelChange,
  formatMetricChange,
  signalDisplayName,
} from '../../lib/formatDelta'
import { filterDeskDeltas } from '../../lib/rankDeltas'
import type { SignalDelta } from '../../types/desk'

type DeltaListProps = {
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

export function DeltaList({ deltas }: DeltaListProps) {
  const visible = filterDeskDeltas(deltas)

  if (visible.length === 0) {
    return <p className="text-sm text-zinc-500">No material regime changes vs previous snapshot.</p>
  }

  return (
    <ul className="divide-y divide-zinc-800 rounded-lg border border-zinc-800">
      {visible.map((delta) => {
        const direction = deltaDirection(delta)
        const deltaText = formatDeltaValue(delta)
        const labelChange = formatLabelChange(delta)
        const metricChange = formatMetricChange(delta)
        const colorClass =
          direction === 'up'
            ? 'text-emerald-400'
            : direction === 'down'
              ? 'text-red-400'
              : 'text-zinc-400'

        return (
          <li key={delta.signal_name} className="flex items-start justify-between gap-4 px-4 py-3">
            <div className="min-w-0">
              <p className="text-sm font-medium text-zinc-200">
                {signalDisplayName(delta.signal_name)}
              </p>
              {labelChange && (
                <p className="mt-0.5 font-mono text-sm text-zinc-300">{labelChange}</p>
              )}
              {metricChange && (
                <p className="mt-1 text-xs text-zinc-500">{metricChange}</p>
              )}
            </div>
            {deltaText && (
              <div
                className={`flex shrink-0 items-center gap-1 font-mono text-sm ${colorClass}`}
              >
                <DirectionIcon direction={direction} />
                <span>{deltaText}</span>
              </div>
            )}
          </li>
        )
      })}
    </ul>
  )
}
