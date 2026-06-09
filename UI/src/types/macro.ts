export type MacroObservation = {
  observation_date: string
  value: number
  unit: string
  fetched_at: string
}

export type MacroSeriesData = {
  schema_version: string
  deterministic: boolean
  source: string
  series_id: string
  title: string | null
  units: string | null
  frequency: string | null
  category: string | null
  limit: number
  count: number
  observations: MacroObservation[]
}
