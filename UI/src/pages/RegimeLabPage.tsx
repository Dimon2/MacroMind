import { useState } from 'react'
import { CompositePills } from '../components/brief/CompositePills'
import { MarketStateTable } from '../components/brief/MarketStateTable'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { DataNotes } from '../components/lab/DataNotes'
import { EpisodeList } from '../components/lab/EpisodeList'
import { LabCardsGrid } from '../components/lab/LabCardsGrid'
import { LabHeader } from '../components/lab/LabHeader'
import { useRegimeLab } from '../hooks/useRegimeLab'

const LAB_MIN_DATE = '1993-01-29'

function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

export function RegimeLabPage() {
  const {
    episodes,
    episodesLoading,
    episodesError,
    selectedDate,
    setSelectedDate,
    data,
    computeLoading,
    computeError,
  } = useRegimeLab()

  const [customDate, setCustomDate] = useState('')

  function handleCustomCompute() {
    if (!customDate) return
    setSelectedDate(customDate)
  }

  if (episodesLoading) {
    return <LoadingState message="Loading episodes…" />
  }

  if (episodesError) {
    return <ErrorState message={episodesError} />
  }

  return (
    <div className="space-y-6">
      {data && !computeLoading && <LabHeader data={data} />}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-3">
          <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">
            Crisis episodes
          </h2>
          <EpisodeList
            episodes={episodes}
            selectedDate={selectedDate}
            onSelect={setSelectedDate}
          />
        </aside>

        <div className="space-y-6">
          <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">
              Custom date
            </h2>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <input
                type="date"
                min={LAB_MIN_DATE}
                max={todayIso()}
                value={customDate}
                onChange={(e) => setCustomDate(e.target.value)}
                className="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1.5 font-mono text-sm text-zinc-200"
              />
              <button
                type="button"
                onClick={handleCustomCompute}
                disabled={!customDate}
                className="rounded-md bg-zinc-700 px-3 py-1.5 text-sm font-medium text-zinc-100 transition-colors hover:bg-zinc-600 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Compute
              </button>
            </div>
          </section>

          {computeLoading && (
            <LoadingState message="Loading historical data…" />
          )}

          {computeError && <ErrorState message={computeError} />}

          {data && !computeLoading && !computeError && (
            <>
              <CompositePills cards={data.cards} />

              <section>
                <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-zinc-500">
                  Market state
                </h2>
                <MarketStateTable cards={data.cards} />
              </section>

              <section>
                <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-zinc-500">
                  Signal detail
                </h2>
                <LabCardsGrid cards={data.cards} />
              </section>

              <DataNotes notes={data.data_notes} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
