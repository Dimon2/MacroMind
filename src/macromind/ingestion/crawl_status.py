from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macromind.db.repository import CrawlRunRepository


def build_crawl_status(
    crawler_names: tuple[str, ...],
    *,
    repo: CrawlRunRepository | None = None,
) -> dict[str, Any]:
    crawl_repo = repo or CrawlRunRepository()
    last_success = crawl_repo.load_last_success_by_crawler()
    last_run = crawl_repo.load_last_run_by_crawler()
    now = datetime.now(timezone.utc)

    crawlers: dict[str, Any] = {}
    missing: list[str] = []

    for name in crawler_names:
        success = last_success.get(name)
        run = last_run.get(name)
        if success is None and run is None:
            missing.append(name)
            crawlers[name] = {"last_success": None, "last_run": None}
            continue

        entry: dict[str, Any] = {}
        if success is not None:
            age_hours = (now - success.finished_at).total_seconds() / 3600.0
            entry["last_success"] = {
                "finished_at": success.finished_at.isoformat(),
                "rows_persisted": success.rows_persisted,
                "age_hours": round(age_hours, 2),
            }
        else:
            entry["last_success"] = None

        if run is not None:
            last_run_payload: dict[str, Any] = {
                "status": run.status,
                "started_at": run.started_at.isoformat(),
                "finished_at": run.finished_at.isoformat(),
                "rows_persisted": run.rows_persisted,
            }
            if run.error_text:
                last_run_payload["error_text"] = run.error_text
            entry["last_run"] = last_run_payload
        else:
            entry["last_run"] = None

        crawlers[name] = entry

    return {
        "as_of": now.isoformat(),
        "crawlers": crawlers,
        "missing": missing,
    }


def crawl_status_is_healthy(status: dict[str, Any], crawler_names: tuple[str, ...]) -> bool:
    if status.get("missing"):
        return False
    crawlers = status.get("crawlers") or {}
    for name in crawler_names:
        entry = crawlers.get(name) or {}
        last_run = entry.get("last_run")
        if not last_run or last_run.get("status") != "success":
            return False
        if entry.get("last_success") is None:
            return False
    return True
