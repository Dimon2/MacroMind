from __future__ import annotations

import argparse
import json

from ai_market_terminal.runner import CrawlerRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Market Terminal crawler runner")
    parser.add_argument(
        "--crawler",
        type=str,
        default="all",
        help="Crawler name (fred, market, nyfed, polymarket, kalshi) or 'all'",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    runner = CrawlerRunner()
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

