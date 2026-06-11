import { useCallback, useEffect, useState } from 'react'
import { ApiError, fetchRegimeCompute, fetchRegimeEpisodes } from '../lib/api'
import type { RegimeLabData, StressEpisode } from '../types/regimeLab'

const DEFAULT_SHOWCASE_DATE = '2020-03-16'

function labErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 503) {
      return 'FRED API key is not configured on the backend. Add FRED_API_KEY to .env and restart the API.'
    }
    return err.message
  }
  if (err instanceof Error) return err.message
  return 'Failed to load regime lab data'
}

export function useRegimeLab() {
  const [episodes, setEpisodes] = useState<StressEpisode[]>([])
  const [episodesLoading, setEpisodesLoading] = useState(true)
  const [episodesError, setEpisodesError] = useState<string | null>(null)

  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [data, setData] = useState<RegimeLabData | null>(null)
  const [computeLoading, setComputeLoading] = useState(false)
  const [computeError, setComputeError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    setEpisodesLoading(true)
    setEpisodesError(null)

    fetchRegimeEpisodes()
      .then((result) => {
        if (cancelled) return
        setEpisodes(result.episodes)
        const hasShowcase = result.episodes.some((ep) => ep.date === DEFAULT_SHOWCASE_DATE)
        const initial = hasShowcase
          ? DEFAULT_SHOWCASE_DATE
          : result.episodes[0]?.date ?? null
        setSelectedDate(initial)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setEpisodes([])
          setEpisodesError(labErrorMessage(err))
        }
      })
      .finally(() => {
        if (!cancelled) setEpisodesLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!selectedDate) return

    let cancelled = false

    setComputeLoading(true)
    setComputeError(null)

    fetchRegimeCompute(selectedDate)
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setData(null)
          setComputeError(labErrorMessage(err))
        }
      })
      .finally(() => {
        if (!cancelled) setComputeLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [selectedDate])

  const selectDate = useCallback((date: string) => {
    setSelectedDate(date)
  }, [])

  return {
    episodes,
    episodesLoading,
    episodesError,
    selectedDate,
    setSelectedDate: selectDate,
    data,
    computeLoading,
    computeError,
  }
}
