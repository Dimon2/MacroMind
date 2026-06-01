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
        help="Persist crawler output to Postgres (kalshi or fred)",
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

    persist_handlers = {
        "kalshi": runner.persist_kalshi,
        "fred": runner.persist_fred,
    }
    if args.persist and args.crawler in persist_handlers:
        count = persist_handlers[args.crawler]()
        print(json.dumps({"persisted": count}, indent=2))
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
