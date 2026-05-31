from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

OutcomeType = Literal["threshold", "categorical"]

_ABOVE_RE = re.compile(
    r"^above\s+\$?([\d,]+(?:\.\d+)?)\s*(%|k|bps)?$",
    re.IGNORECASE,
)
_BELOW_RE = re.compile(
    r"^below\s+\$?([\d,]+(?:\.\d+)?)\s*(%|k|bps)?$",
    re.IGNORECASE,
)
_AT_LEAST_RE = re.compile(
    r"^(?:at least|>=)\s+\$?([\d,]+(?:\.\d+)?)\s*(%|k|bps)?$",
    re.IGNORECASE,
)
_BPS_RE = re.compile(r"^cut\s+(\d+)\s*bps$", re.IGNORECASE)
_HIKE_BPS_RE = re.compile(r"^hike\s+(\d+)\s*bps$", re.IGNORECASE)
_BEFORE_RE = re.compile(r"^before\s+(.+)$", re.IGNORECASE)
_RANGE_RE = re.compile(
    r"^\$?([\d,]+(?:\.\d+)?)\s*to\s*\$?([\d,]+(?:\.\d+)?)$",
    re.IGNORECASE,
)
_MAINTAIN_RE = re.compile(r"maintain", re.IGNORECASE)

_MONTH_YEAR_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.IGNORECASE,
)
_QUARTER_RE = re.compile(r"\bQ([1-4])\s*(\d{4})\b", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(20\d{2})\b")

_MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}


@dataclass(frozen=True)
class ParsedOutcome:
    outcome_type: OutcomeType
    outcome_label: str
    outcome_key: str
    strike: float | None = None
    strike_op: str | None = None
    unit_hint: str | None = None


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "unknown"


def _parse_number(raw: str, suffix: str | None) -> tuple[float, str | None]:
    value = float(raw.replace(",", ""))
    unit: str | None = None
    if suffix:
        unit = suffix.lower()
        if unit == "k":
            value *= 1000
            unit = "count"
        elif unit == "%":
            unit = "percent"
        elif unit == "bps":
            unit = "bps"
    return value, unit


def parse_outcome(label: str) -> ParsedOutcome:
    text = label.strip()
    normalized = text.lower()

    if match := _ABOVE_RE.match(text):
        strike, unit = _parse_number(match.group(1), match.group(2))
        return ParsedOutcome(
            outcome_type="threshold",
            outcome_label=text,
            outcome_key=f"above_{_slugify(match.group(1))}",
            strike=strike,
            strike_op="above",
            unit_hint=unit or "percent",
        )

    if match := _BELOW_RE.match(text):
        strike, unit = _parse_number(match.group(1), match.group(2))
        return ParsedOutcome(
            outcome_type="threshold",
            outcome_label=text,
            outcome_key=f"below_{_slugify(match.group(1))}",
            strike=strike,
            strike_op="below",
            unit_hint=unit or "percent",
        )

    if match := _AT_LEAST_RE.match(text):
        strike, unit = _parse_number(match.group(1), match.group(2))
        return ParsedOutcome(
            outcome_type="threshold",
            outcome_label=text,
            outcome_key=f"at_least_{_slugify(match.group(1))}",
            strike=strike,
            strike_op="at_least",
            unit_hint=unit or "percent",
        )

    if match := _BPS_RE.search(text):
        bps = int(match.group(1))
        return ParsedOutcome(
            outcome_type="categorical",
            outcome_label=text,
            outcome_key=f"cut_{bps}bps",
            unit_hint="bps",
        )

    if match := _HIKE_BPS_RE.search(text):
        bps = int(match.group(1))
        return ParsedOutcome(
            outcome_type="categorical",
            outcome_label=text,
            outcome_key=f"hike_{bps}bps",
            unit_hint="bps",
        )

    if _MAINTAIN_RE.search(text):
        return ParsedOutcome(
            outcome_type="categorical",
            outcome_label=text,
            outcome_key="maintain_rate",
            unit_hint="bps",
        )

    if match := _BEFORE_RE.match(text):
        window = match.group(1).strip()
        return ParsedOutcome(
            outcome_type="categorical",
            outcome_label=text,
            outcome_key=f"before_{_slugify(window)}",
            unit_hint="date",
        )

    if _RANGE_RE.match(text):
        return ParsedOutcome(
            outcome_type="categorical",
            outcome_label=text,
            outcome_key=_slugify(text),
            unit_hint="percent",
        )

    return ParsedOutcome(
        outcome_type="categorical",
        outcome_label=text,
        outcome_key=_slugify(text),
    )


def parse_reference_period(*texts: str | None) -> str | None:
    combined = " ".join(t for t in texts if t)
    if not combined:
        return None

    if match := _QUARTER_RE.search(combined):
        return f"{match.group(2)}-Q{match.group(1)}"

    month_match = _MONTH_YEAR_RE.search(combined)
    year_match = _YEAR_RE.search(combined)
    if month_match and year_match:
        month = _MONTHS[month_match.group(1).lower()]
        return f"{year_match.group(1)}-{month}"

    if year_match:
        return year_match.group(1)

    return None
