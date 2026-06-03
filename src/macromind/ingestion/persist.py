from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from macromind.db.crawl_run import CrawlRunRecord, CrawlRunStatus, truncate_error_text
from macromind.db.repository import CrawlRunRepository


@dataclass(frozen=True)
class CrawlRunResult:
    crawler: str
    status: CrawlRunStatus
    rows_persisted: int
    started_at: datetime
    finished_at: datetime
    error_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "crawler": self.crawler,
            "status": self.status,
            "rows_persisted": self.rows_persisted,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
        }
        if self.error_text is not None:
            payload["error_text"] = self.error_text
        return payload


@dataclass(frozen=True)
class PersistAllReport:
    counts: dict[str, int]
    runs: list[CrawlRunResult]

    @property
    def any_failed(self) -> bool:
        return any(run.status == "failure" for run in self.runs)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = dict(self.counts)
        out["runs"] = [run.to_dict() for run in self.runs]
        return out


def run_persist_with_logging(
    crawler: str,
    persist_fn: Callable[[], int],
    *,
    repo: CrawlRunRepository | None = None,
) -> CrawlRunResult:
    crawl_repo = repo or CrawlRunRepository()
    started_at = datetime.now(timezone.utc)
    status: CrawlRunStatus = "success"
    rows_persisted = 0
    error_text: str | None = None

    try:
        rows_persisted = persist_fn()
    except Exception as exc:
        status = "failure"
        error_text = truncate_error_text(str(exc))
    finally:
        finished_at = datetime.now(timezone.utc)
        crawl_repo.record_run(
            CrawlRunRecord(
                crawler=crawler,
                started_at=started_at,
                finished_at=finished_at,
                status=status,
                rows_persisted=rows_persisted,
                error_text=error_text,
            )
        )

    return CrawlRunResult(
        crawler=crawler,
        status=status,
        rows_persisted=rows_persisted,
        started_at=started_at,
        finished_at=finished_at,
        error_text=error_text,
    )


def run_persist_all_with_logging(
    handlers: dict[str, Callable[[], int]],
    crawler_order: tuple[str, ...],
    *,
    repo: CrawlRunRepository | None = None,
) -> PersistAllReport:
    crawl_repo = repo or CrawlRunRepository()
    counts: dict[str, int] = {}
    runs: list[CrawlRunResult] = []

    for name in crawler_order:
        if name not in handlers:
            continue
        result = run_persist_with_logging(name, handlers[name], repo=crawl_repo)
        runs.append(result)
        counts[name] = result.rows_persisted if result.status == "success" else 0

    counts["total"] = sum(counts.values())
    return PersistAllReport(counts=counts, runs=runs)
