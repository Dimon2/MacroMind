from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.calculators import (
    compute_growth_regime,
    compute_inflation_regime,
    compute_liquidity_regime,
    compute_macro_implied_inflation_prob,
    compute_market_state,
    compute_rates_curve_proxy,
    compute_risk_regime,
)
from macromind.signals.models import SignalResult


class SignalService:
    def compute_results(self, observations: list[NormalizedObservation]) -> list[SignalResult]:
        risk = compute_risk_regime(observations)
        curve = compute_rates_curve_proxy(observations)
        pm_inflation = compute_macro_implied_inflation_prob(observations)
        liquidity = compute_liquidity_regime(observations)
        inflation = compute_inflation_regime(observations)
        growth = compute_growth_regime(observations)
        market = compute_market_state(
            {
                "risk_regime": risk,
                "liquidity_regime": liquidity,
                "inflation_regime": inflation,
                "growth_regime": growth,
            }
        )
        return [risk, curve, pm_inflation, liquidity, inflation, growth, market]

    def compute(self, observations: list[NormalizedObservation]) -> dict[str, Any]:
        results = self.compute_results(observations)
        coverage = {
            "computed": sum(1 for result in results if result.status == "computed"),
            "skipped": sum(1 for result in results if result.status == "skipped"),
            "total": len(results),
        }
        as_of = (
            max((result.as_of for result in results), default=datetime.now(timezone.utc)).isoformat()
        )
        return {
            "as_of": as_of,
            "coverage": coverage,
            "signals": [result.to_dict() for result in results],
        }
