import { PhaseBadge } from './PhaseBadge'
import type { RegimeLabData } from '../../types/regimeLab'

type LabHeaderProps = {
  data: RegimeLabData
}

export function LabHeader({ data }: LabHeaderProps) {
  const { coverage, episode } = data

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-zinc-500">Regime Lab</p>
          <p className="mt-1 font-mono text-sm text-emerald-400">{data.composite ?? '—'}</p>
          {episode && (
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span className="text-sm text-zinc-300">{episode.note}</span>
              <PhaseBadge phase={episode.phase} />
            </div>
          )}
        </div>
        <div className="text-right text-xs text-zinc-500">
          <p>schema {data.schema_version}</p>
          <p className="mt-1 font-mono">query {data.query_date}</p>
          <p className="mt-1">
            coverage {coverage.computed}/{coverage.total} computed
            {coverage.skipped > 0 && ` (${coverage.skipped} skipped)`}
          </p>
        </div>
      </div>
      <p className="mt-2 text-xs text-zinc-600">
        as of {new Date(data.as_of).toLocaleString()}
      </p>
    </div>
  )
}
