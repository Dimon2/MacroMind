import type { DeskData } from '../types/desk'
import type { MacroSeriesData } from '../types/macro'
import type { RegimeLabData, RegimeLabEpisodesData } from '../types/regimeLab'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '')

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function parseErrorMessage(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string | unknown }
    if (typeof body.detail === 'string') return body.detail
    if (body.detail != null) return JSON.stringify(body.detail)
  } catch {
    // ignore non-JSON body
  }
  return res.statusText || `HTTP ${res.status}`
}

async function apiGet<T>(path: string): Promise<T> {
  const url = `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
  const res = await fetch(url)
  if (!res.ok) {
    throw new ApiError(await parseErrorMessage(res), res.status)
  }
  return res.json() as Promise<T>
}

export function fetchDeskLatest(): Promise<DeskData> {
  return apiGet<DeskData>('/desk/latest')
}

export function fetchMacroSeries(
  seriesId: string,
  options?: { limit?: number; source?: 'fred' | 'yfinance' },
): Promise<MacroSeriesData> {
  const params = new URLSearchParams()
  if (options?.limit != null) params.set('limit', String(options.limit))
  if (options?.source) params.set('source', options.source)
  const query = params.toString()
  const path = `/macro/${encodeURIComponent(seriesId)}${query ? `?${query}` : ''}`
  return apiGet<MacroSeriesData>(path)
}

export function fetchRegimeEpisodes(): Promise<RegimeLabEpisodesData> {
  return apiGet<RegimeLabEpisodesData>('/lab/regime/episodes')
}

export function fetchRegimeCompute(date: string): Promise<RegimeLabData> {
  const params = new URLSearchParams({ date })
  return apiGet<RegimeLabData>(`/lab/regime/compute?${params}`)
}
