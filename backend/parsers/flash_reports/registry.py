from __future__ import annotations

from .base import FlashReportParser
from .format_2002 import Format2002Parser


PARSER_REGISTRY: dict[str, type[FlashReportParser]] = {
    "format_2002": Format2002Parser,
}


def get_parser(format_name: str) -> FlashReportParser:
    parser_class = PARSER_REGISTRY.get(format_name)

    if parser_class is None:
        raise ValueError(
            f"No parser registered for format: {format_name}"
        )

    return parser_class()


def detect_format(report_date: str) -> str:
    """
    Determine which parser format applies to a report.

    The 2001–2002 reports currently inspected share the
    same sector-wise project-table structure.
    """

    year = report_date[:4]

    if year in {"2001", "2002"}:
        return "format_2002"

    raise ValueError(
        f"No known parser format for report date: {report_date}"
    )
