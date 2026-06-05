from __future__ import annotations

import json
from datetime import date
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

import main as main_module
from macromind.brief.pipeline import NoSnapshotError
from macromind.ingestion.persist import CrawlRunResult, PersistAllReport


def _success_result(crawler: str, rows: int) -> CrawlRunResult:
    from datetime import datetime, timezone

    now = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)
    return CrawlRunResult(
        crawler=crawler,
        status="success",
        rows_persisted=rows,
        started_at=now,
        finished_at=now,
    )


def test_migrate_only_exits_without_running_crawlers() -> None:
    with (
        patch.object(main_module, "run_migrations") as migrate,
        patch.object(main_module, "CrawlerRunner") as runner_cls,
        patch.object(main_module.sys, "argv", ["main.py", "--migrate"]),
    ):
        main_module.main()
    migrate.assert_called_once()
    runner_cls.assert_not_called()


def test_migrate_then_crawl_status() -> None:
    buf = StringIO()
    with (
        patch.object(main_module, "run_migrations") as migrate,
        patch.object(main_module, "build_crawl_status", return_value={"missing": []}) as status,
        patch.object(main_module, "crawl_status_is_healthy", return_value=True),
        patch.object(main_module.sys, "argv", ["main.py", "--migrate", "--crawl-status"]),
        patch.object(main_module.sys, "stdout", buf),
    ):
        main_module.main()
    migrate.assert_called_once()
    status.assert_called_once()
    assert json.loads(buf.getvalue()) == {"missing": []}


def test_snapshot_signals_prints_payload() -> None:
    payload = {
        "snapshot_date": "2026-06-02",
        "saved": 3,
        "deltas": [],
        "previous_snapshot_date": None,
    }
    buf = StringIO()
    with (
        patch.object(main_module, "run_snapshot_signals", return_value=payload),
        patch.object(main_module.sys, "argv", ["main.py", "--snapshot-signals"]),
        patch.object(main_module.sys, "stdout", buf),
    ):
        main_module.main()
    assert json.loads(buf.getvalue()) == payload


def test_snapshot_signals_excludes_persist() -> None:
    with patch.object(
        main_module.sys, "argv", ["main.py", "--snapshot-signals", "--persist-all"]
    ):
        with pytest.raises(SystemExit):
            main_module.main()


def test_signals_and_snapshot_signals_mutually_exclusive() -> None:
    with patch.object(
        main_module.sys, "argv", ["main.py", "--signals", "--snapshot-signals"]
    ):
        with pytest.raises(SystemExit):
            main_module.main()


def test_crawl_status_exits_one_when_unhealthy() -> None:
    with (
        patch.object(main_module, "build_crawl_status", return_value={"missing": ["fred"]}),
        patch.object(main_module, "crawl_status_is_healthy", return_value=False),
        patch.object(main_module.sys, "argv", ["main.py", "--crawl-status"]),
    ):
        with pytest.raises(SystemExit) as exc:
            main_module.main()
        assert exc.value.code == 1


def test_no_args_prints_help_and_exits() -> None:
    with patch.object(main_module.sys, "argv", ["main.py"]):
        with pytest.raises(SystemExit) as exc:
            main_module.main()
        assert exc.value.code == 2


def test_migrate_then_persist_all() -> None:
    report = PersistAllReport(
        counts={"fred": 1, "kalshi": 2, "market": 3, "total": 6},
        runs=[_success_result("fred", 1), _success_result("kalshi", 2), _success_result("market", 3)],
    )
    buf = StringIO()
    with (
        patch.object(main_module, "run_migrations") as migrate,
        patch.object(main_module, "run_persist_all_with_logging", return_value=report),
        patch.object(main_module.sys, "argv", ["main.py", "--migrate", "--persist-all"]),
        patch.object(main_module.sys, "stdout", buf),
    ):
        main_module.main()
    migrate.assert_called_once()
    assert json.loads(buf.getvalue())["total"] == 6


def test_persist_all_runs_all_handlers() -> None:
    runner = MagicMock()
    report = PersistAllReport(
        counts={"fred": 13, "kalshi": 5, "market": 8, "total": 26},
        runs=[
            _success_result("fred", 13),
            _success_result("kalshi", 5),
            _success_result("market", 8),
        ],
    )
    buf = StringIO()
    with (
        patch.object(main_module, "CrawlerRunner", return_value=runner),
        patch.object(main_module, "run_persist_all_with_logging", return_value=report) as persist_all,
        patch.object(main_module.sys, "argv", ["main.py", "--persist-all"]),
        patch.object(main_module.sys, "stdout", buf),
    ):
        main_module.main()
    payload = json.loads(buf.getvalue())
    assert payload["fred"] == 13
    assert payload["kalshi"] == 5
    assert payload["market"] == 8
    assert payload["total"] == 26
    assert len(payload["runs"]) == 3
    persist_all.assert_called_once()


def test_brief_prints_markdown() -> None:
    brief = "# MacroMind Daily Brief — 2026-06-05\n\n## Market state"
    buf = StringIO()
    with (
        patch.object(main_module, "run_brief", return_value=brief),
        patch.object(main_module.sys, "argv", ["main.py", "--brief"]),
        patch.object(main_module.sys, "stdout", buf),
    ):
        main_module.main()
    assert buf.getvalue().strip() == brief


def test_brief_exits_one_when_no_snapshot() -> None:
    stderr = StringIO()
    with (
        patch.object(
            main_module,
            "run_brief",
            side_effect=NoSnapshotError(date(2026, 6, 5)),
        ),
        patch.object(main_module.sys, "argv", ["main.py", "--brief"]),
        patch.object(main_module.sys, "stderr", stderr),
    ):
        with pytest.raises(SystemExit) as exc:
            main_module.main()
        assert exc.value.code == 1
    assert "--snapshot-signals" in stderr.getvalue()


def test_brief_and_snapshot_signals_mutually_exclusive() -> None:
    with patch.object(main_module.sys, "argv", ["main.py", "--brief", "--snapshot-signals"]):
        with pytest.raises(SystemExit):
            main_module.main()


def test_persist_market_only() -> None:
    runner = MagicMock()
    result = _success_result("market", 8)
    buf = StringIO()
    with (
        patch.object(main_module, "CrawlerRunner", return_value=runner),
        patch.object(main_module, "run_persist_with_logging", return_value=result),
        patch.object(main_module.sys, "argv", ["main.py", "--crawler", "market", "--persist"]),
        patch.object(main_module.sys, "stdout", buf),
    ):
        main_module.main()
    payload = json.loads(buf.getvalue())
    assert payload == {
        "crawler": "market",
        "persisted": 8,
        "run": result.to_dict(),
    }
