import { Link, useParams } from 'react-router-dom'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { useMacroSeries } from '../hooks/useMacroSeries'

export function MacroPage() {
  const { seriesId = '' } = useParams<{ seriesId: string }>()
  const { data, loading, error } = useMacroSeries(seriesId)

  if (loading) return <LoadingState message="Loading series…" />
  if (error) return <ErrorState message={error} />
  if (!data) return <ErrorState message="No series data." />

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-zinc-500">
        <Link to="/" className="text-zinc-400 hover:text-zinc-200">
          Desk
        </Link>
        <span>/</span>
        <span className="font-mono text-zinc-300">{data.series_id}</span>
      </div>

      <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <h2 className="text-lg font-medium text-zinc-100">
          {data.title ?? data.series_id}
        </h2>
        <p className="mt-1 text-sm text-zinc-500">
          {data.source} · {data.frequency ?? '—'} · {data.units ?? '—'}
        </p>
        <p className="mt-4 text-xs text-zinc-500">
          Chart placeholder — {data.count} observations (mock)
        </p>
      </div>

      <div className="overflow-x-auto rounded-lg border border-zinc-800">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-zinc-800 bg-zinc-900/60 text-xs uppercase text-zinc-500">
            <tr>
              <th className="px-4 py-2">Date</th>
              <th className="px-4 py-2">Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {data.observations.map((obs) => (
              <tr key={obs.observation_date}>
                <td className="px-4 py-2 font-mono text-zinc-400">{obs.observation_date}</td>
                <td className="px-4 py-2 font-mono text-zinc-200">{obs.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
