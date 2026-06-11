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
        {cards.growth.unrate && (
          <>
            <p className="mt-2 text-zinc-500">UNRATE (published month)</p>
            <p>Latest: {cards.growth.unrate.latest}%</p>
            <p>Prior: {cards.growth.unrate.prior}%</p>
            <p>Delta: {cards.growth.unrate.delta_pp} pp</p>
          </>
        )}
      </RegimeCard>

      <RegimeCard title="Credit" regime={cards.credit.regime}>
        {Object.entries(cards.credit.series).map(([key, s]) => (
          <p key={key}>
            {key}: {s.value}
            {s.change_pct != null && ` (${s.change_pct > 0 ? '+' : ''}${s.change_pct}%)`}
          </p>
        ))}
      </RegimeCard>
    </div>
  )
}
