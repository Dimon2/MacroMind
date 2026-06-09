import { useEffect, useState } from 'react'
import { deskFixture } from '../mocks/desk.fixture'
import type { DeskData } from '../types/desk'

export function useDesk() {
  const [data, setData] = useState<DeskData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error] = useState<string | null>(null)

  useEffect(() => {
    // TODO: replace with custom API hook call
    setData(deskFixture)
    setLoading(false)
  }, [])

  return { data, loading, error }
}
