from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg

from ai_market_terminal.settings import get_settings


def get_connection() -> psycopg.Connection:
    return psycopg.connect(get_settings().database_url)


@contextmanager
def connection_scope() -> Iterator[psycopg.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
