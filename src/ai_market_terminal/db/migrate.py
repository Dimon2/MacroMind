from __future__ import annotations

import sys
from pathlib import Path

from ai_market_terminal.db.connection import connection_scope
from ai_market_terminal.settings import get_settings


def run_migrations() -> None:
    settings = get_settings()
    migrations_dir = Path(__file__).resolve().parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        print("[migrate] No migration files found")
        return

    target = settings.database_url.split("@")[-1]
    with connection_scope() as conn:
        for migration_path in migration_files:
            sql = migration_path.read_text(encoding="utf-8")
            print(f"[migrate] Applying {migration_path.name} to {target}")
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
