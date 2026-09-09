from __future__ import annotations

from pathlib import Path

import pdfplumber

from .base import FlashReportParser
from .format_2002 import Format2002Parser
from .format_2009 import Format2009Parser


PARSER_REGISTRY: dict[str, type[FlashReportParser]] = {
    "format_2002": Format2002Parser,
    "format_2009": Format2009Parser,
}


def get_parser(format_name: str) -> FlashReportParser:
    parser_class = PARSER_REGISTRY.get(format_name)

    if parser_class is None:
        raise ValueError(
            f"No parser registered for format: {format_name}"
        )

    return parser_class()


def detect_format(pdf_path: Path, report_date: str) -> str:
    """
    Determine the parser format from the actual report structure.

    Most reports through 2009 use the 9-column project table handled
    by Format2002Parser. March 2009 introduced a distinct 10-column
    project-table structure, so format detection must inspect the PDF
    rather than relying only on the year.
    """

    year = report_date[:4]

    if year not in {
        "2001",
        "2002",
        "2003",
        "2004",
        "2005",
        "2006",
        "2007",
        "2008",
        "2009",
    }:
        raise ValueError(
            f"No known parser format for report date: {report_date}"
        )

    if year == "2009":
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = (page.extract_text() or "").upper()

                if (
                    "ADDL. DELAY DURING MONTH" in text
                    and "ANTICIPATED COST" in text
                    and "MILESTONES ACHIEVED/TOTAL" in text
                ):
                    return "format_2009"

    return "format_2002"
