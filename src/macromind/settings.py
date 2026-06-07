from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str
    kalshi_api_base: str
    fred_api_key: str
    api_host: str
    api_port: int
    repo_root: Path

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql://admin:password@localhost:5432/market_db",
            ),
            kalshi_api_base=os.getenv(
                "KALSHI_API_BASE",
                "https://external-api.kalshi.com/trade-api/v2",
            ).rstrip("/"),
            fred_api_key=os.getenv("FRED_API_KEY", "").strip(),
            api_host=os.getenv("API_HOST", "127.0.0.1"),
            api_port=int(os.getenv("API_PORT", "8000")),
            repo_root=_REPO_ROOT,
        )


def get_settings() -> Settings:
    return Settings.from_env()
