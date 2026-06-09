import {
  fedKalshiMarkets,
  formatPmMarketLine,
  inflationPmMarkets,
} from '../../lib/overlays'
import type { DeskOverlays } from '../../types/desk'

type DeskOverlaysDetailProps = {
  overlays: DeskOverlays
}

export function DeskOverlaysDetail({ overlays }: DeskOverlaysDetailProps) {
  const inflationMarkets = inflationPmMarkets(overlays)
  const fedMarkets = fedKalshiMarkets(overlays)
  const fedRate = overlays.fed_compare.effective_rate

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <h3 className="text-sm font-medium text-zinc-200">Inflation prediction market</h3>
        <p className="mt-1 text-xs text-zinc-500">
          Traders&apos; priced probability for a specific inflation threshold on Kalshi.
        </p>
        <p className="mt-2 text-xs text-zinc-600">status: {overlays.inflation_pm.status}</p>

        {inflationMarkets.length === 0 ? (
          <p className="mt-3 text-sm text-zinc-500">No markets in snapshot</p>
        ) : (
          <ul className="mt-3 divide-y divide-zinc-800">
            {inflationMarkets.map((market, i) => {
              const line = formatPmMarketLine(market)
              return (
                <li key={market.market_ticker ?? i} className="py-3 first:pt-0">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm leading-snug text-zinc-200">{line.claim}</p>
                    {line.probability && (
                      <p className="shrink-0 font-mono text-sm font-medium text-zinc-100">
                        {line.probability}
                      </p>
                    )}
                  </div>
                  <p className="mt-1.5 text-xs text-zinc-500">{line.source}</p>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <h3 className="text-sm font-medium text-zinc-200">Fed funds rate</h3>
        <p className="mt-1 text-xs text-zinc-500">
          Current effective rate (FRED) vs Kalshi fed decision contracts when available.
        </p>
        <p className="mt-2 text-xs text-zinc-600">status: {overlays.fed_compare.status}</p>
        <p className="mt-3 font-mono text-lg text-zinc-100">
          {fedRate != null ? `${fedRate}%` : '—'}
          <span className="ml-2 text-xs font-sans text-zinc-500">effective · FRED</span>
        </p>

        {fedMarkets.length === 0 ? (
          <p className="mt-3 text-sm text-zinc-500">No Kalshi fed markets in snapshot</p>
        ) : (
          <ul className="mt-3 divide-y divide-zinc-800">
            {fedMarkets.map((market, i) => {
              const line = formatPmMarketLine(market)
              return (
                <li key={market.market_ticker ?? i} className="py-3 first:pt-0">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm leading-snug text-zinc-200">{line.claim}</p>
                    {line.probability && (
                      <p className="shrink-0 font-mono text-sm font-medium text-zinc-100">
                        {line.probability}
                      </p>
                    )}
                  </div>
                  <p className="mt-1.5 text-xs text-zinc-500">{line.source}</p>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
