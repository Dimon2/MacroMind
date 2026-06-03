from __future__ import annotations

from unittest.mock import MagicMock

from macromind.ingestion.persist import run_persist_all_with_logging, run_persist_with_logging


def test_run_persist_with_logging_success() -> None:
    repo = MagicMock()
    result = run_persist_with_logging("fred", lambda: 7, repo=repo)
    assert result.status == "success"
    assert result.rows_persisted == 7
    repo.record_run.assert_called_once()


def test_run_persist_with_logging_failure_still_records() -> None:
    repo = MagicMock()

    def boom() -> int:
        raise RuntimeError("api down")

    result = run_persist_with_logging("kalshi", boom, repo=repo)
    assert result.status == "failure"
    assert result.rows_persisted == 0
    assert "api down" in (result.error_text or "")
    repo.record_run.assert_called_once()


def test_run_persist_all_continues_after_failure() -> None:
    repo = MagicMock()
    calls: list[str] = []

    def fred() -> int:
        calls.append("fred")
        return 1

    def kalshi() -> int:
        calls.append("kalshi")
        raise ValueError("kalshi fail")

    def market() -> int:
        calls.append("market")
        return 3

    report = run_persist_all_with_logging(
        {"fred": fred, "kalshi": kalshi, "market": market},
        ("fred", "kalshi", "market"),
        repo=repo,
    )
    assert calls == ["fred", "kalshi", "market"]
    assert report.any_failed
    assert report.counts["fred"] == 1
    assert report.counts["kalshi"] == 0
    assert report.counts["market"] == 3
    assert report.counts["total"] == 4
    assert len(report.runs) == 3
    assert repo.record_run.call_count == 3
