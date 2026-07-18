# base class for scanners

from abc import ABC, abstractmethod
from typing import Any

from .models import EntitySpan


class PiiScanner(ABC):
    # base for pluggable scanners

    @property
    @abstractmethod
    def tier(self) -> int:
        # used for diagnostics
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        # human readable name
        raise NotImplementedError

    @abstractmethod
    def scan(
        self,
        text: str,
        unit_id: str = "",
        part: str = "",
        context: dict[str, Any] | None = None,
    ) -> list[EntitySpan]:
        # scans text and returns spans
        raise NotImplementedError
