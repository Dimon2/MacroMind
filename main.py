from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from macromind.db.migrate import run_migrations
from macromind.ingestion.crawl_status import build_crawl_status, crawl_status_is_healthy
from macromind.ingestion.persist import run_persist_all_with_logging, run_persist_with_logging
from macromind.runner import CrawlerRunner
from macromind.signals.pipeline import load_observations_and_compute, run_snapshot_signals

PERSIST_CRAWLERS = ("fred", "kalshi", "market")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MacroMind — ingestion and signals CLI")
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
    parser.add_argument(
        "--signals",
        action="store_true",
        help="Compute signals from persisted DB observations (read-only, no crawler run).",
    )
    parser.add_argument(
        "--snapshot-signals",
        action="store_true",
        help="Compute signals, upsert daily snapshots, and include day-over-day deltas (DB write).",
    )
    parser.add_argument(
        "--crawl-status",
        action="store_true",
        help="Print last crawl run / last success per persisted crawler (read-only, no fetch).",
    )
    return parser


def _persist_handlers(runner: CrawlerRunner) -> dict[str, Callable[[], int]]:
    return {
        "fred": runner.persist_fred,
        "kalshi": runner.persist_kalshi,
        "market": runner.persist_market,
    }


def _run_signals() -> dict[str, Any]:
    return load_observations_and_compute()


def _is_standalone_action(args: argparse.Namespace) -> bool:
    return args.signals or args.crawl_status or args.snapshot_signals


def _validate_standalone_exclusivity(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    standalone_flags = []
    if args.signals:
        standalone_flags.append("--signals")
    if args.snapshot_signals:
        standalone_flags.append("--snapshot-signals")
    if args.crawl_status:
        standalone_flags.append("--crawl-status")

    if len(standalone_flags) > 1:
        parser.error(
            f"Only one standalone action allowed; got: {', '.join(standalone_flags)}"
        )

    wants_run = args.crawler is not None
    wants_persist = args.persist or args.persist_all
    if standalone_flags and (wants_run or wants_persist):
        parser.error(
            f"{standalone_flags[0]} cannot be combined with crawler/persist flags"
        )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    wants_run = args.crawler is not None
    wants_persist = args.persist or args.persist_all
    standalone_action = _is_standalone_action(args)

    if args.migrate:
        run_migrations()
        if not wants_run and not wants_persist and not standalone_action:
            return

    _validate_standalone_exclusivity(parser, args)

    if not wants_run and not wants_persist and not standalone_action:
        parser.print_help(sys.stderr)
        print(
            "\nSpecify an action: --migrate, --signals, --snapshot-signals, --crawl-status, "
            "--persist-all, --crawler NAME [--persist], or --crawler all",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.signals:
        print(json.dumps(_run_signals(), indent=2))
        return

    if args.snapshot_signals:
        print(json.dumps(run_snapshot_signals(), indent=2))
        return

    if args.crawl_status:
        status = build_crawl_status(PERSIST_CRAWLERS)
        print(json.dumps(status, indent=2))
        if not crawl_status_is_healthy(status, PERSIST_CRAWLERS):
            sys.exit(1)
        return

    runner = CrawlerRunner()
    handlers = _persist_handlers(runner)

    if args.persist_all:
        report = run_persist_all_with_logging(handlers, PERSIST_CRAWLERS)
        print(json.dumps(report.to_dict(), indent=2))
        if report.any_failed:
            sys.exit(1)
        return

    if args.persist:
        if args.crawler is None:
            parser.error("--persist requires --crawler NAME or use --persist-all")
        if args.crawler not in handlers:
            parser.error(
                f"--persist supports {', '.join(PERSIST_CRAWLERS)} only; got {args.crawler!r}"
            )
        result = run_persist_with_logging(args.crawler, handlers[args.crawler])
        print(
            json.dumps(
                {
                    "crawler": args.crawler,
                    "persisted": result.rows_persisted,
                    "run": result.to_dict(),
                },
                indent=2,
            )
        )
        if result.status == "failure":
            sys.exit(1)
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
