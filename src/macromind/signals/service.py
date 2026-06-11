from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macromind.market.normalized_observation import NormalizedObservation
from macromind.signals.calculators import (
    compute_credit_regime,
    compute_growth_regime,
    compute_inflation_regime,
    compute_liquidity_level_regime,
    compute_liquidity_trend_regime,
    compute_market_state,
    compute_risk_regime,
)
from macromind.signals.models import SignalResult
from macromind.signals.overlays import (
    build_fed_rate_context,
    build_inflation_pm_overlay,
    build_liquidity_context,
)


class SignalService:
    def compute_results(self, observations: list[NormalizedObservation]) -> list[SignalResult]:
        risk = compute_risk_regime(observations)
        liquidity_trend = compute_liquidity_trend_regime(observations)
        liquidity_level = compute_liquidity_level_regime(observations)
        inflation = compute_inflation_regime(observations)
        growth = compute_growth_regime(observations)
        credit = compute_credit_regime(observations)
        market = compute_market_state(
            {
                "risk_regime": risk,
                "liquidity_level_regime": liquidity_level,
                "inflation_regime": inflation,
                "growth_regime": growth,
                "credit_regime": credit,
            }
        )
        liquidity_ctx = build_liquidity_context(liquidity_level, liquidity_trend)
        inflation_pm = build_inflation_pm_overlay(observations)
        fed_ctx = build_fed_rate_context(observations)
        return [
            risk,
            liquidity_trend,
            liquidity_level,
            inflation,
            growth,
            credit,
            market,
            liquidity_ctx,
            inflation_pm,
            fed_ctx,
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
