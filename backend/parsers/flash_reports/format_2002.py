from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pdfplumber

from .base import FlashReportParser


DATE_RE = re.compile(r"^(\d{1,2})/(\d{4})$")
NUMBER_RE = re.compile(r"^-?\d+(?:,\d{3})*(?:\.\d+)?$")


KNOWN_AGENCIES = {
    "NPCIL",
    "ECL",
    "CCL",
    "SCCL",
    "NLC",
    "NCL",
    "BVFC",
    "HFC",
    "NALCO",
    "NMDC",
    "IOC",
    "BPCL",
    "HPCL",
    "ONGCL",
    "ONGC",
    "P.GRID",
    "NHPC",
    "NTPC",
    "NJPC",
    "SCR",
    "ER",
    "NR",
    "CR",
    "WR",
    "SER",
    "ECOR",
    "NWR",
    "SR",
    "SECR",
    "WCR",
    "NCR",
    "NEFR",
    "RVNL",
    "MTP",
    "JNPT",
    "NMPT",
    "PORTS",
}


SECTORS = {
    "ATOMIC ENERGY",
    "COAL",
    "FERTILISERS",
    "MINES",
    "STEEL",
    "PETROLEUM",
    "POWER",
    "HEALTH & FW",
    "RAILWAYS",
    "ROAD TRANSPORT & HIGHWAYS",
    "SHIPPING & PORTS",
    "URBAN DEVELOPMENT",
}


def clean(value: Any) -> str:
    """
    Normalize extracted PDF cell text.
    """

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).replace("\n", " "),
    ).strip()


def parse_number(value: str) -> float | None:
    """
    Parse a numeric value from the report.
    """

    value = clean(value)

    if value in {"", "-", "–", "—"}:
        return None

    value = value.replace(",", "")

    if not NUMBER_RE.fullmatch(value):
        return None

    return float(value)


def parse_date_token(value: str) -> str | None:
    """
    Convert MM/YYYY into YYYY-MM.
    """

    value = clean(value).strip("()[]")

    if value in {"", "-", "–", "—"}:
        return None

    match = DATE_RE.fullmatch(value)

    if not match:
        return None

    month = int(match.group(1))
    year = int(match.group(2))

    if not 1 <= month <= 12:
        return None

    return f"{year:04d}-{month:02d}"


def split_marked(
    value: str,
) -> tuple[str | None, str | None, str | None]:
    """
    Split report notation into:

        original
        revised
        anticipated

    Example:

        184.55 (403.96) [403.96]

    becomes:

        184.55
        403.96
        403.96

    The parser uses the actual markers rather than positional
    assumptions.
    """

    text = str(value or "").replace("\n", " ")

    original_match = re.search(
        r"(?<![\w\]])"
        r"(-?\d+(?:,\d{3})*(?:\.\d+)?)",
        text,
    )

    revised_match = re.search(
        r"\(\s*"
        r"(-?\d+(?:,\d{3})*(?:\.\d+)?)"
        r"\s*\)",
        text,
    )

    anticipated_match = re.search(
        r"\[\s*"
        r"(-?\d+(?:,\d{3})*(?:\.\d+)?)"
        r"\s*\]",
        text,
    )

    original = (
        original_match.group(1)
        if original_match
        else None
    )

    revised = (
        revised_match.group(1)
        if revised_match
        else None
    )

    anticipated = (
        anticipated_match.group(1)
        if anticipated_match
        else None
    )

    return original, revised, anticipated


def split_dates(
    value: str,
) -> tuple[str | None, str | None, str | None]:
    """
    Split report date notation into:

        original
        revised
        anticipated

    Example:

        1/2007 (-) [7/2006]

    becomes:

        2007-01
        None
        2006-07
    """

    text = str(value or "").replace("\n", " ")

    def first_date(pattern: str) -> str | None:
        match = re.search(pattern, text)

        if not match:
            return None

        return parse_date_token(match.group(1))

    original = first_date(
        r"(?<![\(\[])(?<!\d)"
        r"(\d{1,2}/\d{4})"
        r"(?!\d)(?![\)\]])"
    )

    revised = first_date(
        r"\(\s*(\d{1,2}/\d{4})\s*\)"
    )

    anticipated = first_date(
        r"\[\s*(\d{1,2}/\d{4})\s*\]"
    )

    return original, revised, anticipated


def split_delays(
    value: str,
) -> tuple[float | None, float | None, float | None]:
    """
    Split delay notation into:

        original delay
        revised delay
        additional delay

    Example:

        96 (48) [-]

    becomes:

        96
        48
        None
    """

    text = str(value or "").replace("\n", " ")

    original_match = re.search(
        r"(?<![\w\]\)])"
        r"(-?\d+(?:\.\d+)?)"
        r"(?![\w\)])",
        text,
    )

    revised_match = re.search(
        r"\(\s*(-?\d+(?:\.\d+)?)\s*\)",
        text,
    )

    additional_match = re.search(
        r"\[\s*(-?\d+(?:\.\d+)?)\s*\]",
        text,
    )

    return (
        float(original_match.group(1))
        if original_match
        else None,
        float(revised_match.group(1))
        if revised_match
        else None,
        float(additional_match.group(1))
        if additional_match
        else None,
    )


def parse_milestones(
    value: str,
) -> tuple[int | None, int | None]:
    """
    Parse milestones represented as achieved/total.
    """

    match = re.search(
        r"(\d+)\s*/\s*(\d+)",
        str(value or ""),
    )

    if not match:
        return None, None

    return (
        int(match.group(1)),
        int(match.group(2)),
    )


def extract_agency(
    project_name: str,
) -> str | None:
    """
    Extract an agency only when the parenthesized value is
    a known organization abbreviation.

    Unknown parenthesized text is preserved in project_name
    rather than guessed as an agency.
    """

    candidates = re.findall(
        r"\(([^()]+)\)",
        project_name,
    )

    for candidate in reversed(candidates):
        token = clean(candidate).upper()

        if token in KNOWN_AGENCIES:
            return token

    return None


def detect_sector(
    row: list[str | None],
) -> str | None:
    """
    Detect a sector header row.
    """

    first_cell = clean(row[0]) if row else ""

    if not first_cell:
        return None

    normalized = re.sub(
        r"\s+",
        " ",
        first_cell.upper(),
    ).strip()

    if normalized in SECTORS:
        return normalized

    return None


def is_project_table(
    table: list[list[str | None]],
) -> bool:
    """
    Identify the main sector-wise project table.

    The parser deliberately identifies the table by its structure
    rather than relying on fixed page numbers.
    """

    if not table:
        return False

    if len(table[0]) != 9:
        return False

    header_rows = table[:3]

    header_text = " ".join(
        clean(cell)
        for row in header_rows
        for cell in row
    ).upper()

    required_headers = (
        "NAME OF THE PROJECT",
        "DATE OF",
        "COST",
        "CUMULATIVE EXPENDITURE",
        "MILESTONES",
    )

    return all(
        header in header_text
        for header in required_headers
    )


def parse_report(
    pdf_path: Path,
    report_date: str,
) -> list[dict[str, Any]]:
    """
    Parse one Flash Report into canonical project observations.

    The parser scans every page and dynamically identifies
    the sector-wise project tables.
    """

    observations: list[dict[str, Any]] = []

    current_sector: str | None = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(
            pdf.pages,
            start=1,
        ):
            tables = page.extract_tables()

            for table in tables:
                if not is_project_table(table):
                    continue

                for row in table[2:]:
                    if not row:
                        continue

                    row = [
                        cell.strip()
                        if isinstance(cell, str)
                        else cell
                        for cell in row
                    ]

                    if not any(row):
                        continue

                    sector_candidate = detect_sector(row)

                    if sector_candidate:
                        current_sector = sector_candidate
                        continue

                    serial_match = re.match(
                        r"^\s*(\d+)\s*\.?\s*$",
                        str(row[0] or ""),
                    )

                    if not serial_match:
                        continue

                    serial_no = int(
                        serial_match.group(1)
                    )

                    if len(row) < 9:
                        raise ValueError(
                            f"Malformed project row in "
                            f"{pdf_path.name}, "
                            f"page {page_number}, "
                            f"serial {serial_no}: "
                            f"expected 9 columns, "
                            f"got {len(row)}"
                        )

                    project_name = clean(row[1])

                    if not project_name:
                        raise ValueError(
                            f"Missing project name in "
                            f"{pdf_path.name}, "
                            f"page {page_number}, "
                            f"serial {serial_no}"
                        )

                    (
                        approval_date,
                        approval_date_revised,
                        _,
                    ) = split_dates(row[2])

                    (
                        original_cost_raw,
                        revised_cost_raw,
                        anticipated_cost_raw,
                    ) = split_marked(row[3])

                    (
                        cost_overrun_original_raw,
                        cost_overrun_revised_raw,
                        _,
                    ) = split_marked(row[4])

                    cumulative_expenditure = (
                        parse_number(row[5])
                    )

                    (
                        original_completion_date,
                        revised_completion_date,
                        anticipated_completion_date,
                    ) = split_dates(row[6])

                    (
                        time_overrun_original,
                        time_overrun_revised,
                        additional_delay_months,
                    ) = split_delays(row[7])

                    (
                        milestones_achieved,
                        milestones_total,
                    ) = parse_milestones(row[8])

                    agency = extract_agency(
                        project_name
                    )

                    observations.append(
                        {
                            "observation_id": (
                                f"FR_"
                                f"{report_date.replace('-', '')}"
                                f"_{serial_no:03d}"
                            ),
                            "project_id": None,
                            "project_code": None,
                            "serial_no": serial_no,
                            "project_name": project_name,
                            "agency": agency,
                            "state": None,
                            "sector": current_sector,
                            "report_date": report_date,
                            "approval_date": approval_date,
                            "approval_date_revised": (
                                approval_date_revised
                            ),
                            "original_cost_crore": (
                                parse_number(
                                    original_cost_raw
                                )
                                if original_cost_raw
                                else None
                            ),
                            "revised_cost_crore": (
                                parse_number(
                                    revised_cost_raw
                                )
                                if revised_cost_raw
                                else None
                            ),
                            "anticipated_cost_crore": (
                                parse_number(
                                    anticipated_cost_raw
                                )
                                if anticipated_cost_raw
                                else None
                            ),
                            "cost_overrun_original_crore": (
                                parse_number(
                                    cost_overrun_original_raw
                                )
                                if cost_overrun_original_raw
                                else None
                            ),
                            "cost_overrun_revised_crore": (
                                parse_number(
                                    cost_overrun_revised_raw
                                )
                                if cost_overrun_revised_raw
                                else None
                            ),
                            "cumulative_expenditure_crore": (
                                cumulative_expenditure
                            ),
                            "original_completion_date": (
                                original_completion_date
                            ),
                            "revised_completion_date": (
                                revised_completion_date
                            ),
                            "anticipated_completion_date": (
                                anticipated_completion_date
                            ),
                            "time_overrun_original_months": (
                                time_overrun_original
                            ),
                            "time_overrun_revised_months": (
                                time_overrun_revised
                            ),
                            "additional_delay_months": (
                                additional_delay_months
                            ),
                            "milestones_achieved": (
                                milestones_achieved
                            ),
                            "milestones_total": (
                                milestones_total
                            ),
                            "physical_progress_pct": None,
                            "delay_reason": None,
                            "status": None,
                            "source": {
                                "report": pdf_path.name,
                                "table": (
                                    "Sector-Wise "
                                    "analysis of projects"
                                ),
                                "page": page_number,
                                "serial_no": serial_no,
                            },
                        }
                    )

    return observations


def validate(
    observations: list[dict[str, Any]],
) -> None:
    """
    Validate parsed observations.
    """

    errors: list[str] = []

    serials = [
        observation["serial_no"]
        for observation in observations
    ]

    if not observations:
        errors.append(
            "No project observations found"
        )

    if len(serials) != len(set(serials)):
        duplicates = sorted(
            {
                serial
                for serial in serials
                if serials.count(serial) > 1
            }
        )

        errors.append(
            f"Duplicate serial numbers found: "
            f"{duplicates}"
        )

    for observation in observations:
        observation_id = observation[
            "observation_id"
        ]

        if not observation["project_name"]:
            errors.append(
                f"{observation_id}: "
                f"empty project name"
            )

        achieved = observation[
            "milestones_achieved"
        ]

        total = observation[
            "milestones_total"
        ]

        if (
            achieved is not None
            and total is not None
            and achieved > total
        ):
            errors.append(
                f"{observation_id}: "
                f"milestones achieved "
                f"({achieved}) > total ({total})"
            )

        original_cost = observation[
            "original_cost_crore"
        ]

        if (
            original_cost is not None
            and original_cost < 0
        ):
            errors.append(
                f"{observation_id}: "
                f"negative original cost"
            )

    if errors:
        raise ValueError(
            "\n".join(errors)
        )


class Format2002Parser(FlashReportParser):
    name = "format_2002"

    def parse(
        self,
        pdf_path: Path,
        report_date: str,
    ) -> list[dict[str, Any]]:
        observations = parse_report(
            pdf_path,
            report_date,
        )

        validate(observations)

        return observations
