import { PhaseBadge } from './PhaseBadge'
import type { StressEpisode } from '../../types/regimeLab'

type EpisodeListProps = {
  episodes: StressEpisode[]
  selectedDate: string | null
  onSelect: (date: string) => void
}

export function EpisodeList({ episodes, selectedDate, onSelect }: EpisodeListProps) {
  if (episodes.length === 0) {
    return <p className="text-sm text-zinc-500">No episodes available.</p>
  }

  return (
    <ul className="space-y-1">
      {episodes.map((episode) => {
        const isActive = episode.date === selectedDate
        return (
          <li key={episode.date}>
            <button
              type="button"
              onClick={() => onSelect(episode.date)}
              className={[
                'w-full rounded-lg border px-3 py-2 text-left transition-colors',
                isActive
                  ? 'border-zinc-600 bg-zinc-800'
                  : 'border-zinc-800 bg-zinc-900/40 hover:border-zinc-700 hover:bg-zinc-900/70',
              ].join(' ')}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-zinc-300">{episode.date}</span>
                <PhaseBadge phase={episode.phase} />
              </div>
              <p className="mt-1 text-sm text-zinc-400">{episode.note}</p>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
