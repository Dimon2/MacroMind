from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from macromind.models import DataPoint


class BaseCrawler(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self, config: dict[str, Any]) -> list[DataPoint]:
        """Fetch data points from a source."""
        raise NotImplementedError
