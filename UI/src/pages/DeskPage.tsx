import { CompositeBadge } from '../components/desk/CompositeBadge'
import { DeltaList } from '../components/desk/DeltaList'
import { RegimeCard } from '../components/desk/RegimeCard'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { useDesk } from '../hooks/useDesk'

export function DeskPage() {
  const { data, loading, error } = useDesk()

  if (loading) return <LoadingState message="Loading desk…" />
  if (error) return <ErrorState message={error} />
  if (!data) return <ErrorState message="No desk data." />

  const { cards } = data

  return (
    <div className="space-y-6">
      <CompositeBadge
        composite={data.composite}
        snapshotDate={data.snapshot_date}
        asOf={data.as_of}
      />

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-zinc-500">
          Regime cards
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          <RegimeCard title="Risk" regime={cards.risk.regime}>
            {Object.entries(cards.risk.series).map(([key, s]) => (
              <p key={key}>
                {key}: {s.value}
                {s.change_pct != null && ` (${s.change_pct > 0 ? '+' : ''}${s.change_pct}%)`}
              </p>
            ))}
          </RegimeCard>

          <RegimeCard title="Liquidity" regime={cards.liquidity.regime}>
            <p>Net liq: {cards.liquidity.net_liquidity.level_millions?.toLocaleString()}M</p>
            <p>WoW: {cards.liquidity.net_liquidity.change_wow_pct}%</p>
            <p>M2 YoY: {cards.liquidity.m2.yoy_pct}%</p>
          </RegimeCard>

          <RegimeCard title="Inflation" regime={cards.inflation.regime}>
            <p>Headline YoY: {cards.inflation.headline_yoy_pct}%</p>
            <p>Core YoY: {cards.inflation.core_yoy_pct}%</p>
          </RegimeCard>

          <RegimeCard title="Growth" regime={cards.growth.regime}>
            <p>Curve: {cards.growth.curve.curve_state}</p>
            <p>Spread: {cards.growth.curve.curve_spread}</p>
          </RegimeCard>

          <RegimeCard title="Credit" regime={cards.credit.regime}>
            {Object.entries(cards.credit.series).map(([key, s]) => (
              <p key={key}>{key}: {s.value}</p>
            ))}
          </RegimeCard>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-zinc-500">
          What changed
        </h2>
        <DeltaList deltas={data.deltas} />
      </section>
    </div>
  )
}
