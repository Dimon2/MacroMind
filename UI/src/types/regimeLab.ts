import type { DeskCards, GrowthCard } from './desk'

export type StressPhase =
  | 'detection'
  | 'recovery'
  | 'stress'
  | 'mini_crisis'
  | 'false_alarm'

export type StressEpisode = {
  date: string
  phase: StressPhase
  note: string
}

export type RegimeLabEpisodesData = {
  schema_version: string
  count: number
  episodes: StressEpisode[]
}

export type GrowthCardLab = GrowthCard & {
  unrate?: {
    latest?: number | null
    prior?: number | null
    delta_pp?: number | null
  }
}

export type RegimeLabCards = Omit<DeskCards, 'growth'> & {
  growth: GrowthCardLab
}

export type RegimeLabData = {
  schema_version: string
  deterministic: boolean
  query_date: string
  episode: StressEpisode | null
  as_of: string
  composite: string | null
  coverage: { computed: number; skipped: number; total: number }
  cards: RegimeLabCards
  signals: Array<Record<string, unknown>>
  data_notes: string[]
}
