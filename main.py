from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ai_market_terminal.db.migrate import run_migrations
from ai_market_terminal.runner import CrawlerRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Market Terminal crawler runner")
    parser.add_argument(
        "--crawler",
        type=str,
        default="all",
        help="Crawler name (fred, market, nyfed, polymarket, kalshi) or 'all'",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Persist crawler output to Postgres (kalshi prediction markets)",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Apply database migrations before running",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.migrate:
        run_migrations()

    runner = CrawlerRunner()

    if args.crawler == "kalshi" and args.persist:
        count = runner.persist_kalshi()
        print(json.dumps({"persisted": count}, indent=2))
        return

    if args.crawler == "kalshi":
        snapshots = runner.fetch_kalshi_snapshots()
        serializable = [
            {
                "series_ticker": s.series_ticker,
                "event_ticker": s.event_ticker,
                "market_ticker": s.market_ticker,
                "macro_topic": s.macro_topic,
                "outcome_label": s.outcome_label,
                "yes_probability": s.yes_probability,
                "period_date": s.period_date.isoformat(),
                "url": s.url,
            }
            for s in snapshots
        ]
        print(json.dumps(serializable, indent=2))
        return

    if args.crawler == "all":
        result = runner.run_all()
        serializable = {
            name: [dp.__dict__ for dp in datapoints]
            for name, datapoints in result.items()
        }
        print(json.dumps(serializable, default=str, indent=2))
        return

    result = runner.run_one(args.crawler)
    print(json.dumps([dp.__dict__ for dp in result], default=str, indent=2))


if __name__ == "__main__":
    main()
