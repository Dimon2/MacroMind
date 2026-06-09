import type { DeskData } from '../types/desk'

export const deskFixture: DeskData = {
  schema_version: '1.0',
  deterministic: true,
  snapshot_date: '2026-06-06',
  as_of: '2026-06-06T12:00:00+00:00',
  composite: 'risk_on_easy_stable_expanding_normal',
  previous_snapshot_date: '2026-06-05',
  cards: {
    risk: {
      regime: {
        status: 'computed',
        label: 'risk_on',
        value: 1.0,
        as_of: '2026-06-06T12:00:00+00:00',
      },
      series: {
        SPY: { value: 500.0, change_pct: 0.5 },
        VIX: { value: 18.0 },
      },
    },
    liquidity: {
      regime: {
        status: 'computed',
        label: 'easy',
        value: 1.0,
        as_of: '2026-06-06T12:00:00+00:00',
      },
      net_liquidity: {
        level_millions: 7_000_000,
        change_wow_pct: 0.3,
        as_of: '2026-06-06',
      },
      m2: {
        level_billions: 22800.0,
        change_mom_pct: 0.4,
        yoy_pct: 1.5,
        yoy_status: 'computed',
      },
      series_keys: ['WALCL', 'WTREGEN', 'RRPONTSYD', 'M2SL'],
    },
    inflation: {
      regime: {
        status: 'computed',
        label: 'stable',
        value: 3.0,
        as_of: '2026-06-06T12:00:00+00:00',
      },
      headline_yoy_pct: 2.8,
      core_yoy_pct: 3.1,
      series_keys: ['CPIAUCSL', 'CPILFESL'],
    },
    growth: {
      regime: {
        status: 'computed',
        label: 'expanding',
        value: 1.0,
        as_of: '2026-06-06T12:00:00+00:00',
      },
      curve: {
        curve_spread: 0.25,
        curve_state: 'normal',
        curve_source: 'T10Y2Y',
      },
      series_keys: ['UNRATE'],
    },
    credit: {
      regime: {
        status: 'computed',
        label: 'normal',
        value: 4.0,
        as_of: '2026-06-06T12:00:00+00:00',
      },
      series: {
        BAMLH0A0HYM2: { value: 3.2 },
        HYG: { value: 78.5, change_pct: -0.1 },
      },
    },
  },
  overlays: {
    inflation_pm: {
      markets: [{ yes_probability: 0.4 }],
      status: 'computed',
    },
    fed_compare: {
      effective_rate: 4.25,
      unit: 'percent',
      kalshi_markets: [],
      status: 'computed',
    },
  },
  deltas: [
    {
      signal_name: 'risk_regime',
      status: 'computed',
      value: 1.0,
      label: 'risk_on',
      prev_value: 0.5,
      prev_label: 'neutral',
      value_delta: 0.5,
      label_changed: true,
      comparable: true,
    },
    {
      signal_name: 'liquidity_regime',
      status: 'computed',
      value: 1.0,
      label: 'easy',
      prev_value: 1.0,
      prev_label: 'easy',
      value_delta: 0.0,
      label_changed: false,
      comparable: true,
    },
    {
      signal_name: 'inflation_regime',
      status: 'computed',
      value: 3.0,
      label: 'stable',
      prev_value: 3.1,
      prev_label: 'stable',
      value_delta: -0.1,
      label_changed: false,
      comparable: true,
    },
  ],
}
