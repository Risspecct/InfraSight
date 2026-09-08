from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


MONTH_MAP = {
    "JAN": "01",
    "JANUARY": "01",
    "FEB": "02",
    "FEBRUARY": "02",
    "MAR": "03",
    "MARCH": "03",
    "APR": "04",
    "APRIL": "04",
    "MAY": "05",
    "JUN": "06",
    "JUNE": "06",
    "JUL": "07",
    "JULY": "07",
    "AUG": "08",
    "AUGUST": "08",
    "SEP": "09",
    "SEPT": "09",
    "SEPTEMBER": "09",
    "OCT": "10",
    "OCTOBER": "10",
    "NOV": "11",
    "NOVEMBER": "11",
    "DEC": "12",
    "DECEMBER": "12",
}


def infer_report_date(pdf_path: Path) -> str:
    """
    Infer the report date from the PDF filename.

    Supports both abbreviated and full month names, for example:

        FR_FEB_2002.pdf
        FR_JULY_2001.pdf
        FR_APRIL_2015.pdf

    Returns:
        YYYY-MM
    """

    name = pdf_path.stem.upper()

    month_pattern = "|".join(
        sorted(MONTH_MAP, key=len, reverse=True)
    )

    match = re.search(
        rf"({month_pattern})[_-](20\d{{2}})",
        name,
    )

    if not match:
        raise ValueError(
            f"Could not infer report date from filename: {pdf_path.name}"
        )

    month = MONTH_MAP[match.group(1)]
    year = match.group(2)

    return f"{year}-{month}"


def create_output_directory(
    output_root: Path,
    pdf_path: Path,
) -> Path:
    """
    Create a dedicated output directory for one report.
    """

    report_directory = output_root / pdf_path.stem

    report_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return report_directory


def write_outputs(
    observations: list[dict[str, Any]],
    output_directory: Path,
) -> tuple[Path, Path]:
    """
    Write JSON and CSV representations of parsed observations.
    """

    json_path = output_directory / "observations.json"
    csv_path = output_directory / "observations.csv"

    json_path.write_text(
        json.dumps(
            observations,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    pd.json_normalize(observations).to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig",
    )

    return json_path, csv_path


def build_qa_summary(observations: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a lightweight structural QA summary for one report."""

    serials = [
        observation["serial_no"]
        for observation in observations
        if observation.get("serial_no") is not None
    ]

    duplicate_serials = sorted({
        serial for serial in serials
        if serials.count(serial) > 1
    })

    if serials:
        min_serial = min(serials)
        max_serial = max(serials)
        expected_serials = set(range(min_serial, max_serial + 1))
        missing_serials = sorted(expected_serials - set(serials))
    else:
        min_serial = None
        max_serial = None
        missing_serials = []

    invalid_milestones = 0

    for observation in observations:
        achieved = observation.get("milestones_achieved")
        total = observation.get("milestones_total")

        if achieved is not None and total is not None:
            if achieved < 0 or total < 0 or achieved > total:
                invalid_milestones += 1

    missing_names = sum(
        not observation.get("project_name")
        for observation in observations
    )

    missing_sectors = sum(
        not observation.get("sector")
        for observation in observations
    )

    source_pages = [
        observation["source"]["page"]
        for observation in observations
        if observation.get("source", {}).get("page") is not None
    ]

    checks = {
        "missing_serials": len(missing_serials) == 0,
        "duplicate_serials": len(duplicate_serials) == 0,
        "missing_names": missing_names == 0,
        "missing_sectors": missing_sectors == 0,
        "invalid_milestones": invalid_milestones == 0,
    }

    status = "PASS" if all(checks.values()) else "WARN"

    return {
        "observations": len(observations),
        "serial_min": min_serial,
        "serial_max": max_serial,
        "missing_serials": missing_serials,
        "duplicate_serials": duplicate_serials,
        "missing_names": missing_names,
        "missing_sectors": missing_sectors,
        "invalid_milestones": invalid_milestones,
        "source_page_min": min(source_pages) if source_pages else None,
        "source_page_max": max(source_pages) if source_pages else None,
        "status": status,
    }
