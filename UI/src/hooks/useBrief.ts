import { useEffect, useState } from 'react'
import { briefFixture } from '../mocks/brief.fixture'

export function useBrief() {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error] = useState<string | null>(null)

  useEffect(() => {
    // TODO: replace with custom API hook call
    setContent(briefFixture)
    setLoading(false)
  }, [])

  return { content, loading, error }
}
