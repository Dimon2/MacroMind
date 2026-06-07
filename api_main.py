#!/usr/bin/env python3
"""Run the MacroMind read-only HTTP API."""

from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from macromind.settings import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "macromind.api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
