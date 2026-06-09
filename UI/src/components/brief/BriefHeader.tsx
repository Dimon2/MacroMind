type BriefHeaderProps = {
  snapshotDate: string
  previousSnapshotDate: string | null
}

export function BriefHeader({ snapshotDate, previousSnapshotDate }: BriefHeaderProps) {
  return (
    <header className="flex items-start justify-between gap-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Daily brief
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-100">
          MacroMind Daily Brief
        </h1>
      </div>
      <div className="text-right">
        <p className="font-mono text-sm text-zinc-200">{snapshotDate}</p>
        {previousSnapshotDate && (
          <p className="mt-0.5 text-xs text-zinc-500">prev: {previousSnapshotDate}</p>
        )}
      </div>
    </header>
  )
}
