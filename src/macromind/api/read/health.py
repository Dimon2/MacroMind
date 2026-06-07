from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macromind.brief.context import PERSIST_CRAWLERS
from macromind.db.connection import get_connection
from macromind.ingestion.crawl_status import build_crawl_status, crawl_status_is_healthy

from macromind.api.serializers import SCHEMA_VERSION


def ping_db() -> bool:
    conn = get_connection()
    try:
        conn.execute("SELECT 1")
        return True
    except Exception:
        return False
    finally:
        conn.close()


def build_health_response(*, include_freshness: bool = False) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    db_ok = ping_db()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "error",
        "as_of": now.isoformat(),
    }

    if include_freshness:
        freshness = build_crawl_status(PERSIST_CRAWLERS)
        payload["freshness"] = freshness
        payload["healthy"] = crawl_status_is_healthy(freshness, PERSIST_CRAWLERS)

    return payload
