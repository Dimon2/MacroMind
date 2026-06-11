export type RegimeBlock = {
  status: string
  label: string | null
  value: number | null
  reason?: string | null
  as_of?: string
}

export type RiskCard = {
  regime: RegimeBlock
  series: Record<string, { value: number; change_pct?: number | null }>
}

export type LiquidityMatrix = {
  key?: string | null
  interpretation?: string | null
}

export type LiquidityLevelInputs = {
  vs_52w_pct?: number | null
  walcl_26w_pct?: number | null
  drain_26w_pct?: number | null
  components_scored?: number | null
  components_total?: number | null
}

export type LiquidityCard = {
  regime: RegimeBlock
  level: RegimeBlock
  trend: RegimeBlock
  matrix: LiquidityMatrix
  net_liquidity: {
    level_millions?: number | null
    change_wow_pct?: number | null
    as_of?: string | null
  }
  level_inputs: LiquidityLevelInputs
  m2: {
    level_billions?: number | null
    change_mom_pct?: number | null
    yoy_pct?: number | null
    yoy_status?: string | null
  }
  series_keys: string[]
}

export type InflationCard = {
  regime: RegimeBlock
  headline_yoy_pct?: number | null
  core_yoy_pct?: number | null
  series_keys: string[]
}

export type GrowthCard = {
  regime: RegimeBlock
  curve: {
    curve_spread?: number | null
    curve_state?: string | null
    curve_source?: string | null
  }
  series_keys: string[]
}

export type CreditCard = {
  regime: RegimeBlock
  series: Record<string, { value: number; change_pct?: number | null }>
}

export type DeskCards = {
  risk: RiskCard
  liquidity: LiquidityCard
  inflation: InflationCard
  growth: GrowthCard
  credit: CreditCard
}

export type SignalDelta = {
  signal_name: string
  status: string
  value: number | null
  label: string | null
  prev_value: number | null
  prev_label: string | null
  value_delta: number | null
  label_changed: boolean
  comparable: boolean
}

export type DeskOverlays = {
  inflation_pm: {
    markets: Array<Record<string, unknown>>
    status: string
    reason?: string | null
  }
  fed_compare: {
    effective_rate: number | null
    unit?: string | null
    kalshi_markets: Array<Record<string, unknown>>
    status: string
    reason?: string | null
  }
}

export type DeskData = {
  schema_version: string
  deterministic: boolean
  snapshot_date: string
  as_of: string
  composite: string | null
  cards: DeskCards
  overlays: DeskOverlays
  deltas: SignalDelta[]
  previous_snapshot_date: string | null
}
