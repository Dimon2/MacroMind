from __future__ import annotations

FRED_SOURCE = "fred"

# Tier-1 macro series used by regime calculators
REGIME_SERIES_IDS: tuple[str, ...] = (
    "CPIAUCSL",
    "CPILFESL",
    "UNRATE",
    "WALCL",
    "RRPONTSYD",
    "WTREGEN",
    "M2SL",
)

REGIME_HISTORY_LAST_N = 60
