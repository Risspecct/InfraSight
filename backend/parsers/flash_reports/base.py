from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class FlashReportParser(ABC):
    """
    Common interface for all MoSPI Flash Report format parsers.
    """

    name: str

    @abstractmethod
    def parse(
        self,
        pdf_path: Path,
        report_date: str,
    ) -> list[dict[str, Any]]:
        """
        Parse one Flash Report PDF into canonical project observations.
        """
        raise NotImplementedError
