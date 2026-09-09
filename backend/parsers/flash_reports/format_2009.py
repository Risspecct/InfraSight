from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pdfplumber

from .base import FlashReportParser


DATE_RE = re.compile(r"^(\d{1,2})/(\d{4})$")
NUMBER_RE = re.compile(r"^-?\d+(?:,\d{3})*(?:\.\d+)?$")
SERIAL_RE = re.compile(r"^\d{1,3}$")
MILESTONE_RE = re.compile(r"^\d+\s*/\s*\d+$")
PROJECT_CODE_RE = re.compile(r"\[([A-Za-z0-9]+)\]")

SERIAL_X_MIN = 80
SERIAL_X_MAX = 115

APPROVAL_X_MIN = 235
APPROVAL_X_MAX = 290

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


COLUMN_RANGES = {
    "serial": (90, 112),
    "project": (112, 240),
    "approval": (238, 285),
    "cost": (285, 335),
    "anticipated_cost": (335, 375),
    "expenditure": (375, 417),
    "commissioning": (417, 460),
    "anticipated_completion": (460, 495),
    "delay": (495, 535),
    "milestones": (535, 595),
}


def clean(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).replace("\n", " "),
    ).strip()


def parse_number(value: str) -> float | None:
    value = clean(value)

    if value in {"", "-", "–", "—"}:
        return None

    value = value.replace(",", "")

    if not NUMBER_RE.fullmatch(value):
        return None

    return float(value)


def parse_date(value: str) -> str | None:
    value = clean(value)

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


def first_non_dash(values: list[str]) -> list[str]:
    return [
        value
        for value in values
        if value not in {"", "-", "–", "—"}
    ]


def parse_original_revised_dates(
    values: list[str],
) -> tuple[str | None, str | None]:
    dates = [
        value
        for value in values
        if DATE_RE.fullmatch(value)
    ]

    original = (
        parse_date(dates[0])
        if dates
        else None
    )

    revised = (
        parse_date(dates[1])
        if len(dates) > 1
        else None
    )

    return original, revised


def parse_original_revised_numbers(
    values: list[str],
) -> tuple[float | None, float | None]:
    numbers = [
        parse_number(value)
        for value in values
        if parse_number(value) is not None
    ]

    original = numbers[0] if numbers else None
    revised = numbers[1] if len(numbers) > 1 else None

    return original, revised


def parse_milestones(
    values: list[str],
) -> tuple[int | None, int | None]:
    for value in values:
        match = MILESTONE_RE.fullmatch(value)

        if not match:
            continue

        achieved, total = value.split("/")

        return int(achieved), int(total)

    return None, None


def extract_project_code(
    project_name: str,
) -> str | None:
    matches = PROJECT_CODE_RE.findall(project_name)

    if not matches:
        return None

    return matches[-1]


def extract_agency(
    project_name: str,
) -> str | None:
    """
    March 2009 project names frequently contain agency
    abbreviations in parentheses.

    We extract the final parenthesized token when present,
    but do not guess from arbitrary text.
    """

    matches = re.findall(
        r"\(([^()]+)\)",
        project_name,
    )

    if not matches:
        return None

    candidate = clean(matches[-1])

    if not candidate:
        return None

    return candidate


def detect_sector_heading(row: list[dict[str, Any]]) -> str | None:
    """
    Detect a standalone sector heading from one physical PDF row.

    Sector headings appear as their own physical rows, e.g.
    "Atomic Energy", "Civil Aviation", "Coal", etc.
    """
    row_text = " ".join(
        clean(word.get("text", ""))
        for word in sorted(row, key=lambda x: float(x["x0"]))
    )

    normalized = re.sub(r"\s+", " ", row_text.upper()).strip()

    if normalized in SECTORS:
        return normalized

    return None


def detect_sector_total(
    project_name: str,
) -> str | None:
    """
    Detect a sector subtotal marker embedded at the end
    of a project row.

    Example:
        "... - Total Mines" -> "MINES"
    """

    normalized = re.sub(
        r"\s+",
        " ",
        project_name.upper(),
    ).strip()

    for sector in SECTORS:
        marker = f"TOTAL {sector}"

        if marker in normalized:
            return sector

    return None


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


def group_words_into_rows(
    words: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    """
    Group PDF words by their vertical position.

    Words whose top coordinates are within a small tolerance
    belong to the same physical text line.
    """

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
    low, high = COLUMN_RANGES[column]

    selected = [
        word
        for word in words
        if low <= float(word["x0"]) < high
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


def build_project_rows(words, current_sector=None):
    physical_rows = group_words_into_rows(words)

    logical_rows = []
    current_project = []
    table_complete = False

    for physical_row in physical_rows:

        row_text = " ".join(
            clean(word.get("text", ""))
            for word in sorted(
                physical_row,
                key=lambda x: float(x["x0"])
            )
        )

        normalized = re.sub(
            r"\s+",
            " ",
            row_text.upper()
        ).strip()

        # The primary detailed table ends here.
        if normalized.startswith("GRAND TOTAL"):
            if current_project:
                logical_rows.append({
                    "words": current_project,
                    "serial": _extract_serial(current_project),
                    "sector": current_sector,
                })
                current_project = []

            table_complete = True
            break

        sector_heading = detect_sector_heading(physical_row)

        if sector_heading:
            if current_project:
                logical_rows.append({
                    "words": current_project,
                    "serial": _extract_serial(current_project),
                    "sector": current_sector,
                })
                current_project = []

            current_sector = sector_heading
            continue

        serial_words = [
            word
            for word in physical_row
            if SERIAL_X_MIN <= float(word["x0"]) <= SERIAL_X_MAX
            and float(word["top"]) >= 165
            and SERIAL_RE.fullmatch(
                clean(word.get("text", ""))
            )
        ]

        if serial_words:
            approval_words = [
                word
                for word in physical_row
                if APPROVAL_X_MIN
                <= float(word["x0"])
                <= APPROVAL_X_MAX
            ]

            approval_text = " ".join(
                clean(word.get("text", ""))
                for word in sorted(
                    approval_words,
                    key=lambda x: float(x["x0"])
                )
            )

            has_approval_date = any(
                DATE_RE.fullmatch(token)
                for token in approval_text.split()
            )

            if not has_approval_date:
                continue

            if current_project:
                logical_rows.append({
                    "words": current_project,
                    "serial": _extract_serial(current_project),
                    "sector": current_sector,
                })

            current_project = list(physical_row)

        elif current_project:
            current_project.extend(physical_row)

    if current_project:
        logical_rows.append({
            "words": current_project,
            "serial": _extract_serial(current_project),
            "sector": current_sector,
        })

    logical_rows = [
        row
        for row in logical_rows
        if row["serial"] is not None
    ]

    return logical_rows, current_sector, table_complete


def _extract_serial(
    words: list[dict[str, Any]],
) -> int | None:
    candidates = [
        clean(word.get("text", ""))
        for word in words
        if (
            COLUMN_RANGES["serial"][0]
            <= float(word["x0"])
            < COLUMN_RANGES["serial"][1]
        )
    ]

    for candidate in candidates:
        if SERIAL_RE.fullmatch(candidate):
            serial = int(candidate)

            if 1 <= serial <= 999:
                return serial

    return None


def parse_project_row(
    words: list[dict[str, Any]],
    serial_no: int,
    report_date: str,
    page_number: int,
    sector: str | None,
) -> dict[str, Any] | None:
    serial_no = int(serial_no)
    project_values = get_column_values(
        words,
        "project",
    )

    project_name = " ".join(project_values)
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

    # Remove the source code from the canonical name.
    project_name = re.sub(
        r"\s*\[[A-Za-z0-9]+\]\s*",
        " ",
        project_name,
    )

    project_name = re.sub(
        r"\s+",
        " ",
        project_name,
    ).strip()

    approval_values = get_column_values(
        words,
        "approval",
    )

    cost_values = get_column_values(
        words,
        "cost",
    )

    anticipated_cost_values = get_column_values(
        words,
        "anticipated_cost",
    )

    expenditure_values = get_column_values(
        words,
        "expenditure",
    )

    commissioning_values = get_column_values(
        words,
        "commissioning",
    )

    anticipated_completion_values = get_column_values(
        words,
        "anticipated_completion",
    )

    delay_values = get_column_values(
        words,
        "delay",
    )

    milestone_values = get_column_values(
        words,
        "milestones",
    )

    (
        approval_date,
        approval_date_revised,
    ) = parse_original_revised_dates(
        approval_values
    )

    (
        original_cost,
        revised_cost,
    ) = parse_original_revised_numbers(
        cost_values
    )

    anticipated_cost = None

    for value in anticipated_cost_values:
        parsed = parse_number(value)

        if parsed is not None:
            anticipated_cost = parsed
            break

    cumulative_expenditure = None

    for value in expenditure_values:
        parsed = parse_number(value)

        if parsed is not None:
            cumulative_expenditure = parsed
            break

    (
        original_completion_date,
        revised_completion_date,
    ) = parse_original_revised_dates(
        commissioning_values
    )

    anticipated_completion_date = None

    for value in anticipated_completion_values:
        if DATE_RE.fullmatch(value):
            anticipated_completion_date = parse_date(
                value
            )
            break

    additional_delay_months = None

    for value in delay_values:
        parsed = parse_number(value)

        if parsed is not None:
            additional_delay_months = parsed
            break

    (
        milestones_achieved,
        milestones_total,
    ) = parse_milestones(
        milestone_values
    )

    return {
        "observation_id": (
            f"FR_"
            f"{report_date.replace('-', '')}"
            f"_{serial_no:03d}"
        ),
        "project_id": None,
        "project_code": project_code,
        "serial_no": serial_no,
        "project_name": project_name,
        "agency": extract_agency(project_name),
        "state": None,
        "sector": sector,
        "report_date": report_date,
        "approval_date": approval_date,
        "approval_date_revised": approval_date_revised,
        "original_cost_crore": original_cost,
        "revised_cost_crore": revised_cost,
        "anticipated_cost_crore": anticipated_cost,
        "cost_overrun_original_crore": None,
        "cost_overrun_revised_crore": None,
        "cumulative_expenditure_crore": cumulative_expenditure,
        "original_completion_date": original_completion_date,
        "revised_completion_date": revised_completion_date,
        "anticipated_completion_date": (
            anticipated_completion_date
        ),
        "time_overrun_original_months": None,
        "time_overrun_revised_months": None,
        "additional_delay_months": additional_delay_months,
        "milestones_achieved": milestones_achieved,
        "milestones_total": milestones_total,
        "physical_progress_pct": None,
        "delay_reason": None,
        "status": None,
        "source": {
            "report": None,
            "table": (
                "Sector-Wise "
                "analysis of projects"
            ),
            "page": page_number,
            "serial_no": serial_no,
        },
    }


def parse_report(
    pdf_path: Path,
    report_date: str,
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []

    current_sector: str | None = None

    with pdfplumber.open(pdf_path) as pdf:

        for page_number, page in enumerate(pdf.pages, start=1):

            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=3,
                keep_blank_chars=False,
                use_text_flow=False,
            )

            if not words:
                continue

            if not is_table_header(words):
                continue

            rows, current_sector, table_complete = build_project_rows(
                words,
                current_sector,
            )

            for row in rows:
                serial_no = int(row["serial"])

                observation = parse_project_row(
                    row["words"],
                    serial_no,
                    report_date,
                    page_number,
                    row["sector"],
                )

                if observation is None:
                    continue

                observation["source"]["report"] = pdf_path.name
                observation["source"]["page"] = page_number

                observations.append(observation)
            if table_complete:
                break

    return observations


def validate(
    observations: list[dict[str, Any]],
) -> None:

    errors: list[str] = []

    if not observations:
        errors.append(
            "No project observations found"
        )

    serials = [
        observation["serial_no"]
        for observation in observations
    ]

    duplicates = sorted(
        {
            serial
            for serial in serials
            if serials.count(serial) > 1
        }
    )

    if duplicates:
        errors.append(
            f"Duplicate serial numbers found: "
            f"{duplicates}"
        )

    if observations:
        minimum = min(serials)
        maximum = max(serials)

        missing = sorted(
            set(range(minimum, maximum + 1))
            - set(serials)
        )

        if missing:
            errors.append(
                f"Missing serial numbers: {missing}"
            )

    for observation in observations:
        if not observation["project_name"]:
            errors.append(
                f"{observation['observation_id']}: "
                "empty project name"
            )

        achieved = observation[
            "milestones_achieved"
        ]

        total = observation[
            "milestones_total"
        ]

        if achieved > total:
            print(
                f"WARNING: {observation['observation_id']}: "
                f"milestones achieved ({achieved}) > total ({total})"
            )

    if errors:
        raise ValueError(
            "\n".join(errors)
        )


class Format2009Parser(FlashReportParser):
    name = "format_2009"

    def parse(
        self,
        pdf_path: Path,
        report_date: str,
    ) -> list[dict[str, Any]]:
        observations = parse_report(pdf_path, report_date)
        validate(observations)
        return observations
