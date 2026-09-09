from __future__ import annotations

from pathlib import Path

import pdfplumber
import re

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


def _normalize_pdf_text(text: str) -> str:
    """
    Normalize PDF-extracted text for structural format detection.

    PDF extraction can split words such as:
        ANTICI-
        PATED

    into separate lines. Remove those artificial line breaks first,
    then normalize remaining whitespace.
    """
    text = text.upper()

    # Join words broken by PDF line wrapping.
    text = re.sub(r"-\s*\n\s*", "", text)

    # Normalize all remaining whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def detect_format(pdf_path: Path, report_date: str) -> str:
    """
    Detect the parser family required for a Flash Report.

    Detection is based on the structure of the report rather than
    exact text, because PDF extraction can introduce line breaks,
    hyphenation, and spacing differences.
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
        "2010",
    }:
        raise ValueError(
            f"No known parser format for report date: {report_date}"
        )

    if year in ["2009", "2010"]:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                raw_text = page.extract_text() or ""
                text = _normalize_pdf_text(raw_text)

                has_project_column = (
                    "S.NO" in text
                    and "PROJECT" in text
                )

                has_cost_columns = (
                    "COST" in text
                    and "CUMM." in text
                )

                has_delay_column = (
                    "DELAY" in text
                    and "MILESTONES" in text
                )

                if (
                    has_project_column
                    and has_cost_columns
                    and has_delay_column
                ):
                    return "format_2009"

        raise ValueError(
            f"No known parser format for report structure: {pdf_path.name}"
        )

    return "format_2002"
