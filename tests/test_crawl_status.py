from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from macromind.db.crawl_run import CrawlRunRecord
from macromind.ingestion.crawl_status import build_crawl_status, crawl_status_is_healthy

_NOW = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)


def test_build_crawl_status_missing_crawler() -> None:
    repo = MagicMock()
    repo.load_last_success_by_crawler.return_value = {}
    repo.load_last_run_by_crawler.return_value = {}
    status = build_crawl_status(("fred", "kalshi"), repo=repo)
    assert status["missing"] == ["fred", "kalshi"]
    assert status["crawlers"]["fred"]["last_success"] is None


def test_build_crawl_status_with_success() -> None:
    repo = MagicMock()
    record = CrawlRunRecord(
        crawler="fred",
        started_at=_NOW,
        finished_at=_NOW,
        status="success",
        rows_persisted=5,
    )
    repo.load_last_success_by_crawler.return_value = {"fred": record}
    repo.load_last_run_by_crawler.return_value = {"fred": record}
    status = build_crawl_status(("fred",), repo=repo)
    assert status["missing"] == []
    assert status["crawlers"]["fred"]["last_success"]["rows_persisted"] == 5
    assert status["crawlers"]["fred"]["last_run"]["status"] == "success"


def test_crawl_status_is_healthy_false_on_failure() -> None:
    success = CrawlRunRecord("fred", _NOW, _NOW, "success", 1)
    failure = CrawlRunRecord("fred", _NOW, _NOW, "failure", 0, error_text="x")
    status = {
        "missing": [],
        "crawlers": {
            "fred": {
                "last_success": {"finished_at": _NOW.isoformat()},
                "last_run": {"status": "failure"},
            }
        },
    }
    assert crawl_status_is_healthy(status, ("fred",)) is False

    status_ok = {
        "missing": [],
        "crawlers": {
            "fred": {
                "last_success": {"finished_at": _NOW.isoformat()},
                "last_run": {"status": "success"},
            }
        },
    }
    assert crawl_status_is_healthy(status_ok, ("fred",)) is True
