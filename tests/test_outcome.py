from ai_market_terminal.prediction_markets.outcome import parse_outcome, parse_reference_period


def test_parse_above_threshold() -> None:
    parsed = parse_outcome("Above 4.2%")
    assert parsed.outcome_type == "threshold"
    assert parsed.strike == 4.2
    assert parsed.strike_op == "above"
    assert parsed.outcome_key == "above_4_2"


def test_parse_fed_maintain() -> None:
    parsed = parse_outcome("Fed maintains rate")
    assert parsed.outcome_type == "categorical"
    assert parsed.outcome_key == "maintain_rate"


def test_parse_before_date() -> None:
    parsed = parse_outcome("Before 2027")
    assert parsed.outcome_type == "categorical"
    assert parsed.outcome_key == "before_2027"


def test_reference_period_month_year() -> None:
    assert parse_reference_period("Inflation in May (CPI YoY) 2026") == "2026-05"
