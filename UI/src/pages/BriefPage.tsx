import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { useBrief } from '../hooks/useBrief'

export function BriefPage() {
  const { content, loading, error } = useBrief()

  if (loading) return <LoadingState message="Loading brief…" />
  if (error) return <ErrorState message={error} />
  if (!content) return <ErrorState message="No brief content." />

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">
        Daily brief
      </h2>
      <pre className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-900/40 p-4 font-mono text-sm leading-relaxed whitespace-pre-wrap text-zinc-300">
        {content}
      </pre>
    </div>
  )
}
