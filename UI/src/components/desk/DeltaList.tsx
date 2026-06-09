import type { SignalDelta } from '../../types/desk'

type DeltaListProps = {
  deltas: SignalDelta[]
}

export function DeltaList({ deltas }: DeltaListProps) {
  if (deltas.length === 0) {
    return <p className="text-sm text-zinc-500">No deltas available.</p>
  }

  return (
    <ul className="divide-y divide-zinc-800 rounded-lg border border-zinc-800">
      {deltas.map((delta) => (
        <li key={delta.signal_name} className="flex items-center justify-between px-4 py-3">
          <div>
            <p className="font-mono text-sm text-zinc-200">{delta.signal_name}</p>
            <p className="text-xs text-zinc-500">
              {delta.prev_label ?? '—'} → {delta.label ?? '—'}
              {delta.label_changed && (
                <span className="ml-2 text-amber-400">label changed</span>
              )}
            </p>
          </div>
          <div className="text-right">
            {delta.value_delta != null && (
              <p
                className={`font-mono text-sm ${
                  delta.value_delta > 0
                    ? 'text-emerald-400'
                    : delta.value_delta < 0
                      ? 'text-red-400'
                      : 'text-zinc-400'
                }`}
              >
                {delta.value_delta > 0 ? '+' : ''}
                {delta.value_delta.toFixed(2)}
              </p>
            )}
          </div>
        </li>
      ))}
    </ul>
  )
}
