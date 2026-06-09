import type { ReactNode } from 'react'
import type { RegimeBlock } from '../../types/desk'

type RegimeCardProps = {
  title: string
  regime: RegimeBlock
  children?: ReactNode
}

function statusColor(status: string) {
  if (status === 'computed') return 'bg-emerald-900/40 text-emerald-300'
  if (status === 'missing') return 'bg-zinc-800 text-zinc-500'
  return 'bg-amber-900/40 text-amber-300'
}

export function RegimeCard({ title, regime, children }: RegimeCardProps) {
  return (
    <article className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="mb-3 flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium capitalize text-zinc-200">{title}</h3>
        <span
          className={`rounded px-2 py-0.5 text-xs font-medium ${statusColor(regime.status)}`}
        >
          {regime.status}
        </span>
      </div>
      <p className="font-mono text-lg text-zinc-100">
        {regime.label ?? '—'}
      </p>
      {regime.value != null && (
        <p className="mt-1 text-xs text-zinc-500">value: {regime.value}</p>
      )}
      {children && <div className="mt-3 space-y-1 text-xs text-zinc-400">{children}</div>}
    </article>
  )
}
