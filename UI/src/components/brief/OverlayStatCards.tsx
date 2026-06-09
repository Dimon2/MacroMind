import {
  fedKalshiMarkets,
  inflationPmDisplay,
} from '../../lib/overlays'
import type { DeskOverlays } from '../../types/desk'

type OverlayStatCardsProps = {
  overlays: DeskOverlays
}

export function OverlayStatCards({ overlays }: OverlayStatCardsProps) {
  const inflation = inflationPmDisplay(overlays)
  const fedRate = overlays.fed_compare.effective_rate
  const fedMarkets = fedKalshiMarkets(overlays)

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-5">
        <p className="text-xs font-medium text-zinc-400">Inflation prediction market</p>
        {inflation ? (
          <>
            <p className="mt-3 text-3xl font-semibold tracking-tight text-zinc-100">
              {inflation.pct}
            </p>
            <p className="mt-2 text-sm leading-snug text-zinc-200">{inflation.claim}</p>
            <p className="mt-2 text-xs text-zinc-500">{inflation.source}</p>
          </>
        ) : (
          <p className="mt-3 text-sm text-zinc-500">No inflation market data</p>
        )}
      </div>

      <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-5">
        <p className="text-xs font-medium text-zinc-400">Fed funds rate</p>
        <p className="mt-0.5 text-xs text-zinc-600">Effective rate · FRED</p>
        <p className="mt-3 text-3xl font-semibold tracking-tight text-zinc-100">
          {fedRate != null ? `${fedRate}%` : '—'}
        </p>
        {fedMarkets.length > 0 ? (
          <p className="mt-2 text-xs text-zinc-500">
            {fedMarkets.length} Kalshi fed market{fedMarkets.length !== 1 ? 's' : ''} on desk
          </p>
        ) : (
          <p className="mt-2 text-xs text-zinc-500">No Kalshi fed markets in snapshot</p>
        )}
      </div>
    </div>
  )
}
