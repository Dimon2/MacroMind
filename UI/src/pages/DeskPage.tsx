import { Link } from 'react-router-dom'
import { DeltaList } from '../components/desk/DeltaList'
import { DeskHeader } from '../components/desk/DeskHeader'
import { DeskOverlaysDetail } from '../components/desk/DeskOverlaysDetail'
import { RegimeCard } from '../components/desk/RegimeCard'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { useDesk } from '../hooks/useDesk'

function MacroLinks({ keys }: { keys: string[] }) {
  if (keys.length === 0) return null
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {keys.map((key) => (
        <Link
          key={key}
          to={`/macro/${key}`}
          className="font-mono text-xs text-blue-400 hover:text-blue-300"
        >
          {key}
        </Link>
      ))}
    </div>
  )
}

export function DeskPage() {
  const { data, loading, error } = useDesk()

  if (loading) return <LoadingState message="Loading desk…" />
  if (error) return <ErrorState message={error} />
  if (!data) return <ErrorState message="No desk data." />

  const { cards } = data

  return (
    <div className="space-y-6">
      <DeskHeader
        composite={data.composite}
        snapshotDate={data.snapshot_date}
        previousSnapshotDate={data.previous_snapshot_date}
        asOf={data.as_of}
        schemaVersion={data.schema_version}
      />

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-zinc-500">
          Signal detail
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

          <RegimeCard title="Liquidity (level)" regime={cards.liquidity.level}>
            <p className="text-xs text-zinc-500">
              Trend: <span className="font-mono text-zinc-300">{cards.liquidity.trend.label ?? '—'}</span>
            </p>
            {cards.liquidity.matrix.interpretation && (
              <p className="text-xs text-zinc-400">{cards.liquidity.matrix.interpretation}</p>
            )}
            <p>Net liq: {cards.liquidity.net_liquidity.level_millions?.toLocaleString()}M</p>
            <p>WoW: {cards.liquidity.net_liquidity.change_wow_pct}%</p>
            {cards.liquidity.level_inputs.vs_52w_pct != null && (
              <p>vs 52w avg: {cards.liquidity.level_inputs.vs_52w_pct}%</p>
            )}
            <p>M2 YoY: {cards.liquidity.m2.yoy_pct}%</p>
            <MacroLinks keys={cards.liquidity.series_keys} />
          </RegimeCard>

          <RegimeCard title="Inflation" regime={cards.inflation.regime}>
            <p>Headline YoY: {cards.inflation.headline_yoy_pct}%</p>
            <p>Core YoY: {cards.inflation.core_yoy_pct}%</p>
            <MacroLinks keys={cards.inflation.series_keys} />
          </RegimeCard>

          <RegimeCard title="Growth" regime={cards.growth.regime}>
            <p>Curve: {cards.growth.curve.curve_state}</p>
            <p>Spread: {cards.growth.curve.curve_spread}</p>
            <MacroLinks keys={cards.growth.series_keys} />
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

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-zinc-500">
          Prediction markets & rates
        </h2>
        <DeskOverlaysDetail overlays={data.overlays} />
      </section>
    </div>
  )
}
