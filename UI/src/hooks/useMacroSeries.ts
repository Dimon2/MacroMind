import { useEffect, useState } from 'react'
import { ApiError, fetchMacroSeries } from '../lib/api'
import type { MacroSeriesData } from '../types/macro'

function macroErrorMessage(err: unknown, seriesId: string): string {
  if (err instanceof ApiError) {
    if (err.status === 404) {
      return `Series ${seriesId} not found or has no observations in the database.`
    }
    return err.message
  }
  if (err instanceof Error) return err.message
  return 'Failed to load series'
}

export function useMacroSeries(seriesId: string) {
  const [data, setData] = useState<MacroSeriesData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!seriesId) {
      setData(null)
      setLoading(false)
      setError('Series id is required')
      return
    }

    let cancelled = false

    setLoading(true)
    setError(null)

    fetchMacroSeries(seriesId)
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setData(null)
          setError(macroErrorMessage(err, seriesId))
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [seriesId])

  return { data, loading, error }
}
