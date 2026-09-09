from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pdfplumber

from .base import FlashReportParser


# ============================================================
# Constants
# ============================================================

DATE_RE = re.compile(r"^(\d{1,2})/(\d{4})$")
NUMBER_RE = re.compile(r"^-?\d+(?:,\d{3})*(?:\.\d+)?$")
SERIAL_RE = re.compile(r"^\d{1,3}$")
MILESTONE_RE = re.compile(r"^\d+\s*/\s*\d+$")
PROJECT_CODE_RE = re.compile(r"\[([A-Za-z0-9]+)\]")

# October 2011 coordinate layout.
#
# These are deliberately based on the actual October 2011 PDF
# rather than the older March 2009 coordinates.
COLUMN_RANGES = {
    "serial": (80, 95),
    "project": (95, 225),
    "approval": (225, 275),

    # October 2011:
    # Original Cost / Anticipated Cost / Cumulative Expenditure
    "cost": (275, 315),
    "anticipated_cost": (315, 365),
    "expenditure": (365, 405),

    # Original Commissioning / Anticipated Commissioning
    "commissioning": (405, 445),
    "anticipated_completion": (445, 480),

    # Delay w.r.t. Original / Revised
    "delay": (480, 520),

    "milestones": (520, 600),
}


SECTORS = {
    "ATOMIC ENERGY",
    "CIVIL AVIATION",
    "COAL",
    "FERTILISERS",
    "MINES",
    "PETROLEUM",
    "POWER",
    "RAILWAYS",
    "ROAD TRANSPORT & HIGHWAYS",
    "SHIPPING & PORTS",
    "STEEL",
    "TELECOMMUNICATIONS",
    "URBAN DEVELOPMENT",
    "WATER RESOURCES",
}


# ============================================================
# Basic helpers
# ============================================================

def clean(value: str) -> str:
    value = value.replace("\n", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_number(value: str) -> float | None:
    value = clean(value)

    if not value:
        return None

    if not NUMBER_RE.fullmatch(value):
        return None

    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def parse_date_token(value: str) -> str | None:
    value = clean(value)

    match = DATE_RE.fullmatch(value)

    if not match:
        return None

    month, year = match.groups()

    month_int = int(month)

    if not 1 <= month_int <= 12:
        return None

    return f"{year}-{month_int:02d}"


def extract_project_code(project_name: str) -> str | None:
    match = PROJECT_CODE_RE.search(project_name)

    if not match:
        return None

    return match.group(1)


def normalize_project_name(project_name: str) -> str:
    project_name = re.sub(
        r"\s*\[[A-Za-z0-9]+\]\s*",
        " ",
        project_name,
    )

    project_name = re.sub(
        r"\s+",
        " ",
        project_name,
    )

    return project_name.strip()


# ============================================================
# PDF row helpers
# ============================================================

def group_words_into_rows(
    words: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:

    sorted_words = sorted(
        words,
        key=lambda word: (
            float(word["top"]),
            float(word["x0"]),
        ),
    )

    rows: list[list[dict[str, Any]]] = []

    for word in sorted_words:
        top = float(word["top"])

        if not rows:
            rows.append([word])
            continue

        previous_top = float(rows[-1][0]["top"])

        if abs(top - previous_top) <= 2.5:
            rows[-1].append(word)
        else:
            rows.append([word])

    return rows


def get_column_values(
    words: list[dict[str, Any]],
    column: str,
) -> list[str]:

    x_min, x_max = COLUMN_RANGES[column]

    selected = [
        word
        for word in words
        if x_min <= float(word["x0"]) < x_max
    ]

    selected.sort(
        key=lambda word: (
            float(word["top"]),
            float(word["x0"]),
        )
    )

    return [
        clean(word.get("text", ""))
        for word in selected
        if clean(word.get("text", ""))
    ]


# ============================================================
# Header / sector detection
# ============================================================

def is_table_header(
    words: list[dict[str, Any]],
) -> bool:

    text = " ".join(
        clean(word.get("text", ""))
        for word in words
    ).upper()

    return (
        "S.NO" in text
        and "PROJECT" in text
        and "APPROVAL" in text
        and "MILESTONES" in text
    )


def detect_sector_heading(
    row: list[dict[str, Any]],
) -> str | None:

    row_text = " ".join(
        clean(word.get("text", ""))
        for word in sorted(
            row,
            key=lambda x: float(x["x0"]),
        )
    )

    normalized = re.sub(
        r"\s+",
        " ",
        row_text.upper(),
    ).strip()

    if normalized in SECTORS:
        return normalized

    return None


def is_grand_total(
    row: list[dict[str, Any]],
) -> bool:

    row_text = " ".join(
        clean(word.get("text", ""))
        for word in sorted(
            row,
            key=lambda x: float(x["x0"]),
        )
    )

    normalized = re.sub(
        r"\s+",
        " ",
        row_text.upper(),
    ).strip()

    return normalized.startswith("GRAND TOTAL")


# ============================================================
# Serial detection
# ============================================================

def extract_serial_from_row(
    row: list[dict[str, Any]],
) -> int | None:

    candidates = []

    for word in row:
        value = clean(word.get("text", ""))

        if not SERIAL_RE.fullmatch(value):
            continue

        serial = int(value)

        if not 1 <= serial <= 999:
            continue

        x0 = float(word["x0"])

        # Serial numbers in the October 2011 table appear
        # around x=82–90. Keep this deliberately narrow
        # so numeric values elsewhere in the row cannot
        # become false serial numbers.
        if not 80 <= x0 <= 100:
            continue

        candidates.append(
            (
                float(word["top"]),
                x0,
                serial,
            )
        )

    if not candidates:
        return None

    candidates.sort()

    return candidates[0][2]

# ============================================================
# Logical project row construction
# ============================================================
def build_project_rows(
    words: list[dict[str, Any]],
    current_sector: str | None = None,
) -> tuple[
    list[dict[str, Any]],
    str | None,
    bool,
]:

    physical_rows = group_words_into_rows(words)

    logical_rows: list[dict[str, Any]] = []

    current_project: list[dict[str, Any]] = []
    current_project_start: list[dict[str, Any]] | None = None

    table_complete = False

    def flush_current_project():
        nonlocal current_project
        nonlocal current_project_start

        if not current_project:
            return

        serial = None

        if current_project_start is not None:
            serial = extract_serial_from_row(
                current_project_start
            )

        logical_rows.append(
            {
                "words": current_project,
                "serial": serial,
                "sector": current_sector,
            }
        )

        current_project = []
        current_project_start = None

    for physical_row in physical_rows:

        # ----------------------------------------------------
        # Explicit end of primary table
        # ----------------------------------------------------

        if is_grand_total(physical_row):

            flush_current_project()

            table_complete = True
            break

        # ----------------------------------------------------
        # Sector heading
        # ----------------------------------------------------

        sector_heading = detect_sector_heading(
            physical_row
        )

        if sector_heading:

            flush_current_project()

            current_sector = sector_heading
            continue

        # ----------------------------------------------------
        # Detect project-start row
        # ----------------------------------------------------

        serial = extract_serial_from_row(
            physical_row
        )

        if serial is not None:

            approval_words = [
                word
                for word in physical_row
                if (
                    COLUMN_RANGES["approval"][0]
                    <= float(word["x0"])
                    < COLUMN_RANGES["approval"][1]
                )
            ]

            approval_text = " ".join(
                clean(word.get("text", ""))
                for word in sorted(
                    approval_words,
                    key=lambda x: float(x["x0"]),
                )
            )

            has_approval_date = any(
                DATE_RE.fullmatch(token)
                for token in approval_text.split()
            )

            if has_approval_date:

                # New project starts here.
                flush_current_project()

                current_project = list(
                    physical_row
                )

                current_project_start = list(
                    physical_row
                )

                continue

        # ----------------------------------------------------
        # Continuation line
        # ----------------------------------------------------

        if current_project:

            current_project.extend(
                physical_row
            )

    # --------------------------------------------------------
    # Flush final project
    # --------------------------------------------------------

    flush_current_project()

    # --------------------------------------------------------
    # Keep only rows with valid serials
    # --------------------------------------------------------

    logical_rows = [
        row
        for row in logical_rows
        if row["serial"] is not None
    ]

    return (
        logical_rows,
        current_sector,
        table_complete,
    )

# ============================================================
# Field parsers
# ============================================================

def parse_original_revised_dates(
    values: list[str],
) -> tuple[str | None, str | None]:

    dates = [
        parse_date_token(value)
        for value in values
    ]

    dates = [
        value
        for value in dates
        if value is not None
    ]

    if not dates:
        return None, None

    original = dates[0]

    revised = dates[1] if len(dates) >= 2 else None

    return original, revised


def parse_original_revised_cost(
    values: list[str],
) -> tuple[float | None, float | None]:

    numbers = [
        parse_number(value)
        for value in values
    ]

    numbers = [
        value
        for value in numbers
        if value is not None
    ]

    if not numbers:
        return None, None

    original = numbers[0]

    revised = numbers[1] if len(numbers) >= 2 else None

    return original, revised


def parse_milestones(
    values: list[str],
) -> tuple[int | None, int | None]:

    for value in values:

        value = clean(value)

        if not MILESTONE_RE.fullmatch(value):
            continue

        achieved, total = value.split("/")

        return int(achieved), int(total)

    return None, None


def parse_delay(
    values: list[str],
) -> tuple[int | None, int | None]:
    for value in values:
        value = clean(value)

        if value in {"", "-"}:
            continue

        match = re.match(
            r"^(-?\d+)\s*\(([^)]+)\)",
            value,
        )

        if not match:
            continue

        months = int(match.group(1))
        basis = match.group(2).strip().upper()

        if basis.startswith("O"):
            return months, None

        if basis.startswith("R"):
            return None, months

    return None, None

# ============================================================
# Project observation parser
# ============================================================

def parse_project_row(
    words: list[dict[str, Any]],
    serial_no: int,
    report_date: str,
    page_number: int,
    sector: str | None,
) -> dict[str, Any] | None:

    serial_no = int(serial_no)

    # --------------------------------------------------------
    # Project name
    # --------------------------------------------------------

    project_values = get_column_values(
        words,
        "project",
    )

    project_name = " ".join(
        project_values
    )

    project_name = re.sub(
        r"\s+",
        " ",
        project_name,
    ).strip()

    if not project_name:
        return None

    project_code = extract_project_code(
        project_name
    )

    project_name = normalize_project_name(
        project_name
    )

    # --------------------------------------------------------
    # Approval
    # --------------------------------------------------------

    approval_values = get_column_values(
        words,
        "approval",
    )

    approval_dates = [
        parse_date_token(value)
        for value in approval_values
    ]

    approval_dates = [
        value
        for value in approval_dates
        if value is not None
    ]

    approval_date = (
        approval_dates[0]
        if approval_dates
        else None
    )

    approval_date_revised = (
        approval_dates[1]
        if len(approval_dates) >= 2
        else None
    )

    # --------------------------------------------------------
    # Cost
    # --------------------------------------------------------

    cost_values = get_column_values(
        words,
        "cost",
    )

    original_cost, revised_cost = (
        parse_original_revised_cost(
            cost_values
        )
    )

    # --------------------------------------------------------
    # Anticipated cost
    # --------------------------------------------------------

    anticipated_cost_values = (
        get_column_values(
            words,
            "anticipated_cost",
        )
    )

    anticipated_cost = None

    for value in anticipated_cost_values:

        parsed = parse_number(value)

        if parsed is not None:
            anticipated_cost = parsed
            break

    # --------------------------------------------------------
    # Cumulative expenditure
    # --------------------------------------------------------

    expenditure_values = (
        get_column_values(
            words,
            "expenditure",
        )
    )

    cumulative_expenditure = None

    for value in expenditure_values:

        parsed = parse_number(value)

        if parsed is not None:
            cumulative_expenditure = parsed
            break

    # --------------------------------------------------------
    # Commissioning dates
    # --------------------------------------------------------

    commissioning_values = (
        get_column_values(
            words,
            "commissioning",
        )
    )

    original_completion_date, revised_completion_date = (
        parse_original_revised_dates(
            commissioning_values
        )
    )

    # --------------------------------------------------------
    # Anticipated completion
    # --------------------------------------------------------

    anticipated_completion_values = (
        get_column_values(
            words,
            "anticipated_completion",
        )
    )

    anticipated_completion_date = None

    for value in anticipated_completion_values:

        parsed = parse_date_token(value)

        if parsed is not None:
            anticipated_completion_date = parsed
            break

    # --------------------------------------------------------
    # Delay
    # --------------------------------------------------------

    delay_values = get_column_values(
        words,
        "delay",
    )

    time_overrun_original_months, time_overrun_revised_months = (
        parse_delay(delay_values)
    )

    # --------------------------------------------------------
    # Milestones
    # --------------------------------------------------------

    milestone_values = get_column_values(
        words,
        "milestones",
    )

    milestones_achieved, milestones_total = (
        parse_milestones(
            milestone_values
        )
    )

    # --------------------------------------------------------
    # Observation
    # --------------------------------------------------------

    observation = {
        "observation_id": (
            f"FR_{report_date.replace('-', '')}"
            f"_{serial_no:03d}"
        ),

        "project_id": None,

        "project_code": project_code,

        "serial_no": serial_no,

        "project_name": project_name,

        "agency": None,

        "state": None,

        "sector": sector,

        "report_date": report_date,

        "approval_date": approval_date,

        "approval_date_revised": (
            approval_date_revised
        ),

        "original_cost_crore": original_cost,

        "revised_cost_crore": revised_cost,

        "anticipated_cost_crore": anticipated_cost,

        "cost_overrun_original_crore": None,

        "cost_overrun_revised_crore": None,

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
            time_overrun_original_months
        ),
        
        "time_overrun_revised_months": (
            time_overrun_revised_months
        ),
        
        "additional_delay_months": None,

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
            "report": None,
            "table": "Sector Wise Details",
            "page": page_number,
            "serial_no": serial_no,
        },
    }

    return observation


# ============================================================
# Main report parser
# ============================================================

def parse_report(
    pdf_path: Path,
    report_date: str,
) -> list[dict[str, Any]]:

    observations: list[dict[str, Any]] = []

    current_sector: str | None = None

    in_primary_table = False

    with pdfplumber.open(pdf_path) as pdf:

        for page_number, page in enumerate(
            pdf.pages,
            start=1,
        ):

            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=3,
                keep_blank_chars=False,
                use_text_flow=False,
            )

            if not words:
                continue

            # ------------------------------------------------
            # Build page-level text
            # ------------------------------------------------

            page_text = " ".join(
                clean(word.get("text", ""))
                for word in words
            )

            normalized_page_text = re.sub(
                r"\s+",
                " ",
                page_text.upper(),
            ).strip()

            # ------------------------------------------------
            # Find primary detailed table
            # ------------------------------------------------

            if not in_primary_table:

                if "SECTOR WISE DETAILS" not in (
                    normalized_page_text
                ):
                    continue

                in_primary_table = True

            # ------------------------------------------------
            # Parse current primary-table page
            # ------------------------------------------------

            rows, current_sector, table_complete = (
                build_project_rows(
                    words,
                    current_sector,
                )
            )

            for row in rows:

                serial_no = int(
                    row["serial"]
                )

                observation = parse_project_row(
                    row["words"],
                    serial_no,
                    report_date,
                    page_number,
                    row["sector"],
                )

                if observation is None:
                    continue

                observation["source"]["report"] = (
                    pdf_path.name
                )

                observation["source"]["page"] = (
                    page_number
                )

                observations.append(
                    observation
                )

            # ------------------------------------------------
            # Explicit end of primary table
            # ------------------------------------------------

            if table_complete:
                break

    return observations


# ============================================================
# Parser class
# ============================================================

class Format2009Parser(FlashReportParser):

    name = "format_2009"

    def parse(
        self,
        pdf_path: Path,
        report_date: str,
    ) -> list[dict[str, Any]]:

        return parse_report(
            pdf_path,
            report_date,
        )
