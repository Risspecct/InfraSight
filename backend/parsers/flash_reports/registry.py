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

    Handles words split across PDF line breaks, such as:
        Antici-
        pated
    """
    text = text.upper()

    # Join words broken by PDF line wrapping.
    text = re.sub(r"-\s*\n\s*", "", text)

    # Normalize remaining whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def detect_format(pdf_path: Path, report_date: str) -> str:
    """
    Detect the structural parser family used by a Flash Report.

    Parser selection is based on document structure rather than
    publication year because multiple formats may exist within
    the same year.
    """

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw_text = page.extract_text() or ""

            if not raw_text:
                continue

            text = _normalize_pdf_text(raw_text)

            # ---------------------------------------------------------
            # Older / 2002-style structure
            # ---------------------------------------------------------
            if (
                "SL. NO" in text
                and "NAME OF THE PROJECT" in text
                and "DATE OF APPROVAL" in text
                and "COST OVERRUN" in text
                and "CUMULATIVE EXPENDITURE" in text
                and "MILESTONES" in text
            ):
                return "format_2002"

            # ---------------------------------------------------------
            # 2009-style structure
            # ---------------------------------------------------------
            if (
                "S.NO" in text
                and "PROJECT" in text
                and "COST" in text
                and "CUMM." in text
                and "DELAY" in text
                and "MILESTONES" in text
            ):
                return "format_2009"

    raise ValueError(
        f"No known parser format for report structure: {pdf_path.name}"
    )
