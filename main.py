from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ai_market_terminal.db.migrate import run_migrations
from ai_market_terminal.runner import CrawlerRunner

PERSIST_CRAWLERS = ("fred", "kalshi", "market")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Market Terminal crawler runner")
    parser.add_argument(
        "--crawler",
        type=str,
        default=None,
        metavar="NAME",
        help=(
            "Crawler to run (fred, market, nyfed, polymarket, kalshi) or 'all' for preview JSON."
        ),
    )
    persist = parser.add_mutually_exclusive_group()
    persist.add_argument(
        "--persist",
        action="store_true",
        help=f"Persist one crawler to Postgres (with --crawler: {', '.join(PERSIST_CRAWLERS)})",
    )
    persist.add_argument(
        "--persist-all",
        action="store_true",
        help=f"Persist all DB-backed crawlers ({', '.join(PERSIST_CRAWLERS)})",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Apply database migrations before other actions (migrate-only if nothing else)",
    )
    return parser


def _persist_handlers(runner: CrawlerRunner) -> dict[str, Callable[[], int]]:
    return {
        "fred": runner.persist_fred,
        "kalshi": runner.persist_kalshi,
        "market": runner.persist_market,
    }


def _run_persist_all(runner: CrawlerRunner) -> dict[str, int]:
    handlers = _persist_handlers(runner)
    counts: dict[str, int] = {}
    for name in PERSIST_CRAWLERS:
        counts[name] = handlers[name]()
    counts["total"] = sum(counts.values())
    return counts


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    wants_run = args.crawler is not None
    wants_persist = args.persist or args.persist_all

    if args.migrate:
        run_migrations()
        if not wants_run and not wants_persist:
            return

    if not wants_run and not wants_persist:
        parser.print_help(sys.stderr)
        print(
            "\nSpecify an action: --migrate, --persist-all, --crawler NAME [--persist], or --crawler all",
            file=sys.stderr,
        )
        sys.exit(2)

    runner = CrawlerRunner()
    handlers = _persist_handlers(runner)

    if args.persist_all:
        print(json.dumps(_run_persist_all(runner), indent=2))
        return

    if args.persist:
        if args.crawler is None:
            parser.error("--persist requires --crawler NAME or use --persist-all")
        if args.crawler not in handlers:
            parser.error(
                f"--persist supports {', '.join(PERSIST_CRAWLERS)} only; got {args.crawler!r}"
            )
        count = handlers[args.crawler]()
        print(json.dumps({"crawler": args.crawler, "persisted": count}, indent=2))
        return

    if args.crawler == "all":
        result = runner.run_all()
        serializable: dict[str, Any] = {
            name: [dp.__dict__ for dp in datapoints]
            for name, datapoints in result.items()
        }
        print(json.dumps(serializable, default=str, indent=2))
        return

    result = runner.run_one(args.crawler)
    print(json.dumps([dp.__dict__ for dp in result], default=str, indent=2))


if __name__ == "__main__":
    main()
