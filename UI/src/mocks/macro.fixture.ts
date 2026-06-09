import type { MacroSeriesData } from '../types/macro'

export function macroSeriesFixture(seriesId: string): MacroSeriesData {
  const id = seriesId.toUpperCase()
  return {
    schema_version: '1.0',
    deterministic: true,
    source: 'fred',
    series_id: id,
    title: `Mock ${id}`,
    units: 'Percent',
    frequency: 'Daily',
    category: 'macro',
    limit: 30,
    count: 5,
    observations: [
      { observation_date: '2026-06-02', value: 4.2, unit: 'Percent', fetched_at: '2026-06-06T12:00:00+00:00' },
      { observation_date: '2026-06-03', value: 4.25, unit: 'Percent', fetched_at: '2026-06-06T12:00:00+00:00' },
      { observation_date: '2026-06-04', value: 4.3, unit: 'Percent', fetched_at: '2026-06-06T12:00:00+00:00' },
      { observation_date: '2026-06-05', value: 4.28, unit: 'Percent', fetched_at: '2026-06-06T12:00:00+00:00' },
      { observation_date: '2026-06-06', value: 4.32, unit: 'Percent', fetched_at: '2026-06-06T12:00:00+00:00' },
    ],
  }
}
