from __future__ import annotations

import sys
from pathlib import Path

from ai_market_terminal.db.connection import connection_scope
from ai_market_terminal.settings import get_settings


def run_migrations() -> None:
    settings = get_settings()
    migration_path = (
        Path(__file__).resolve().parent / "migrations" / "001_pm_tables.sql"
    )
    sql = migration_path.read_text(encoding="utf-8")
    print(f"[migrate] Applying {migration_path.name} to {settings.database_url.split('@')[-1]}")
    with connection_scope() as conn:
        conn.execute(sql)
    print("[migrate] Done")


def main() -> None:
    try:
        run_migrations()
    except Exception as exc:
        print(f"[migrate] Failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
