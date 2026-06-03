from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

CrawlRunStatus = Literal["success", "failure"]

_MAX_ERROR_TEXT_LEN = 2000


@dataclass(frozen=True)
class CrawlRunRecord:
    crawler: str
    started_at: datetime
    finished_at: datetime
    status: CrawlRunStatus
    rows_persisted: int
    error_text: str | None = None


def truncate_error_text(text: str | None) -> str | None:
    if text is None:
        return None
    if len(text) <= _MAX_ERROR_TEXT_LEN:
        return text
    return text[: _MAX_ERROR_TEXT_LEN - 3] + "..."
