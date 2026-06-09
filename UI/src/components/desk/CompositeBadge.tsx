type CompositeBadgeProps = {
  composite: string | null
  snapshotDate: string
  asOf: string
}

export function CompositeBadge({ composite, snapshotDate, asOf }: CompositeBadgeProps) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3">
      <p className="text-xs uppercase tracking-wider text-zinc-500">Market state</p>
      <p className="mt-1 font-mono text-sm text-emerald-400">
        {composite ?? '—'}
      </p>
      <p className="mt-2 text-xs text-zinc-500">
        Snapshot {snapshotDate} · as of {new Date(asOf).toLocaleString()}
      </p>
    </div>
  )
}
