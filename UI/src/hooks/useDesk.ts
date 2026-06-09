import { useEffect, useState } from 'react'
import { ApiError, fetchDeskLatest } from '../lib/api'
import type { DeskData } from '../types/desk'

function deskErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 404) {
      return 'No signal snapshots yet. Run ingest and --snapshot-signals on the backend.'
    }
    return err.message
  }
  if (err instanceof Error) return err.message
  return 'Failed to load desk data'
}

export function useDesk() {
  const [data, setData] = useState<DeskData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    setLoading(true)
    setError(null)

    fetchDeskLatest()
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setData(null)
          setError(deskErrorMessage(err))
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  return { data, loading, error }
}
