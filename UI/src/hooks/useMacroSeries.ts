import { useEffect, useState } from 'react'
import { macroSeriesFixture } from '../mocks/macro.fixture'
import type { MacroSeriesData } from '../types/macro'

export function useMacroSeries(seriesId: string) {
  const [data, setData] = useState<MacroSeriesData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error] = useState<string | null>(null)

  useEffect(() => {
    // TODO: replace with custom API hook call
    setData(macroSeriesFixture(seriesId))
    setLoading(false)
  }, [seriesId])

  return { data, loading, error }
}
