from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.calculators import (
    compute_growth_regime,
    compute_inflation_regime,
    compute_liquidity_regime,
    compute_macro_implied_inflation_prob,
    compute_rates_curve_proxy,
    compute_risk_regime,
)
from macromind.signals.models import SignalResult


class SignalService:
    def compute_results(self, observations: list[NormalizedObservation]) -> list[SignalResult]:
        return [
            compute_risk_regime(observations),
            compute_rates_curve_proxy(observations),
            compute_macro_implied_inflation_prob(observations),
            compute_liquidity_regime(observations),
            compute_inflation_regime(observations),
            compute_growth_regime(observations),
        ]

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
