type DeskHeaderProps = {
  composite: string | null
  snapshotDate: string
  previousSnapshotDate: string | null
  asOf: string
  schemaVersion: string
}

export function DeskHeader({
  composite,
  snapshotDate,
  previousSnapshotDate,
  asOf,
  schemaVersion,
}: DeskHeaderProps) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-zinc-500">Analyst desk</p>
          <p className="mt-1 font-mono text-sm text-emerald-400">{composite ?? '—'}</p>
        </div>
        <div className="text-right text-xs text-zinc-500">
          <p>schema {schemaVersion}</p>
          <p className="mt-1">snapshot {snapshotDate}</p>
          {previousSnapshotDate && <p>prev {previousSnapshotDate}</p>}
        </div>
      </div>
      <p className="mt-2 text-xs text-zinc-600">
        as of {new Date(asOf).toLocaleString()}
      </p>
    </div>
  )
}
