from __future__ import annotations

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

import main as main_module


def test_migrate_only_exits_without_running_crawlers() -> None:
    with (
        patch.object(main_module, "run_migrations") as migrate,
        patch.object(main_module, "CrawlerRunner") as runner_cls,
        patch.object(main_module.sys, "argv", ["main.py", "--migrate"]),
    ):
        main_module.main()
    migrate.assert_called_once()
    runner_cls.assert_not_called()


def test_no_args_prints_help_and_exits() -> None:
    with patch.object(main_module.sys, "argv", ["main.py"]):
        with pytest.raises(SystemExit) as exc:
            main_module.main()
        assert exc.value.code == 2


def test_migrate_then_persist_all() -> None:
    runner = MagicMock()
    runner.persist_fred.return_value = 1
    runner.persist_kalshi.return_value = 2
    runner.persist_market.return_value = 3
    buf = StringIO()
    with (
        patch.object(main_module, "run_migrations") as migrate,
        patch.object(main_module, "CrawlerRunner", return_value=runner),
        patch.object(main_module.sys, "argv", ["main.py", "--migrate", "--persist-all"]),
        patch.object(main_module.sys, "stdout", buf),
    ):
        main_module.main()
    migrate.assert_called_once()
    assert json.loads(buf.getvalue())["total"] == 6


def test_persist_all_runs_all_handlers() -> None:
    runner = MagicMock()
    runner.persist_fred.return_value = 13
    runner.persist_kalshi.return_value = 5
    runner.persist_market.return_value = 8
    buf = StringIO()
    with (
        patch.object(main_module, "CrawlerRunner", return_value=runner),
        patch.object(main_module.sys, "argv", ["main.py", "--persist-all"]),
        patch.object(main_module.sys, "stdout", buf),
    ):
        main_module.main()
    assert json.loads(buf.getvalue()) == {
        "fred": 13,
        "kalshi": 5,
        "market": 8,
        "total": 26,
    }
    runner.persist_fred.assert_called_once()
    runner.persist_kalshi.assert_called_once()
    runner.persist_market.assert_called_once()


def test_persist_market_only() -> None:
    runner = MagicMock()
    runner.persist_market.return_value = 8
    buf = StringIO()
    with (
        patch.object(main_module, "CrawlerRunner", return_value=runner),
        patch.object(main_module.sys, "argv", ["main.py", "--crawler", "market", "--persist"]),
        patch.object(main_module.sys, "stdout", buf),
    ):
        main_module.main()
    assert json.loads(buf.getvalue()) == {"crawler": "market", "persisted": 8}
    runner.persist_market.assert_called_once()
