import { formatNum, formatPct } from '../../lib/formatNumber'
import { RegimeCard } from '../desk/RegimeCard'
import type { RegimeLabCards } from '../../types/regimeLab'

type LabCardsGridProps = {
  cards: RegimeLabCards
}

export function LabCardsGrid({ cards }: LabCardsGridProps) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <RegimeCard title="Risk" regime={cards.risk.regime}>
        {Object.entries(cards.risk.series).map(([key, s]) => (
          <p key={key}>
            {key}: {formatNum(s.value)}
            {s.change_pct != null && ` (${formatPct(s.change_pct)})`}
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
        <p>WoW: {formatPct(cards.liquidity.net_liquidity.change_wow_pct)}</p>
        {cards.liquidity.level_inputs.vs_52w_pct != null && (
          <p>vs 52w avg: {formatPct(cards.liquidity.level_inputs.vs_52w_pct)}</p>
        )}
        <p>M2 YoY: {formatPct(cards.liquidity.m2.yoy_pct)}</p>
      </RegimeCard>

      <RegimeCard title="Inflation" regime={cards.inflation.regime}>
        <p>Headline YoY: {formatPct(cards.inflation.headline_yoy_pct)}</p>
        <p>Core YoY: {formatPct(cards.inflation.core_yoy_pct)}</p>
      </RegimeCard>

      <RegimeCard title="Growth" regime={cards.growth.regime}>
        <p>Curve: {cards.growth.curve.curve_state}</p>
        <p>Spread: {formatNum(cards.growth.curve.curve_spread)}</p>
        {cards.growth.unrate && (
          <>
            <p className="mt-2 text-zinc-500">UNRATE (published month)</p>
            <p>Latest: {formatNum(cards.growth.unrate.latest)}%</p>
            <p>Prior: {formatNum(cards.growth.unrate.prior)}%</p>
            <p>Delta: {formatNum(cards.growth.unrate.delta_pp)} pp</p>
          </>
        )}
      </RegimeCard>

      <RegimeCard title="Credit" regime={cards.credit.regime}>
        {Object.entries(cards.credit.series).map(([key, s]) => (
          <p key={key}>
            {key}: {formatNum(s.value)}
            {s.change_pct != null && ` (${formatPct(s.change_pct)})`}
          </p>
        ))}
      </RegimeCard>
    </div>
  )
}
