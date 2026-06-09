import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { BriefHeader } from '../components/brief/BriefHeader'
import { CompositePills } from '../components/brief/CompositePills'
import { LlmCommentaryPlaceholder } from '../components/brief/LlmCommentaryPlaceholder'
import { MarketStateTable } from '../components/brief/MarketStateTable'
import { OverlayStatCards } from '../components/brief/OverlayStatCards'
import { TopChangesList } from '../components/brief/TopChangesList'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { useDesk } from '../hooks/useDesk'
import { rankTopDeltas } from '../lib/rankDeltas'

function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">
      {children}
    </h2>
  )
}

export function BriefPage() {
  const { data, loading, error } = useDesk()

  if (loading) return <LoadingState message="Loading brief…" />
  if (error) return <ErrorState message={error} />
  if (!data) return <ErrorState message="No brief data." />

  const topDeltas = rankTopDeltas(data.deltas, 3)

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <BriefHeader
        snapshotDate={data.snapshot_date}
        previousSnapshotDate={data.previous_snapshot_date}
      />

      <CompositePills cards={data.cards} />

      <section>
        <SectionTitle>Market state</SectionTitle>
        <MarketStateTable cards={data.cards} />
      </section>

      <section>
        <SectionTitle>What changed (top 3)</SectionTitle>
        <TopChangesList deltas={topDeltas} />
      </section>

      <section>
        <SectionTitle>Prediction markets & rates</SectionTitle>
        <OverlayStatCards overlays={data.overlays} />
      </section>

      <LlmCommentaryPlaceholder />

      <div className="pt-2 text-center">
        <Link
          to="/desk"
          className="text-sm text-zinc-400 transition-colors hover:text-zinc-200"
        >
          View details →
        </Link>
      </div>
    </div>
  )
}
