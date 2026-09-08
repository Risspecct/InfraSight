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


def build_qa_summary(
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build structural, completeness, and validity QA for one report."""

    serials = [
        observation.get("serial_no")
        for observation in observations
        if observation.get("serial_no") is not None
    ]

    # ---------------------------------------------------------
    # Structural checks
    # ---------------------------------------------------------

    serial_counts: dict[int, int] = {}

    for serial in serials:
        serial_counts[serial] = serial_counts.get(serial, 0) + 1

    duplicate_serials = sorted(
        serial
        for serial, count in serial_counts.items()
        if count > 1
    )

    if serials:
        min_serial = min(serials)
        max_serial = max(serials)

        expected_serials = set(
            range(min_serial, max_serial + 1)
        )

        missing_serials = sorted(
            expected_serials - set(serials)
        )
    else:
        min_serial = None
        max_serial = None
        missing_serials = []

    structural_checks = {
        "has_observations": len(observations) > 0,
        "serial_continuity": len(missing_serials) == 0,
        "duplicate_serials": len(duplicate_serials) == 0,
    }

    # ---------------------------------------------------------
    # Completeness checks
    # ---------------------------------------------------------

    missing_names = sum(
        not observation.get("project_name")
        for observation in observations
    )

    missing_sectors = sum(
        not observation.get("sector")
        for observation in observations
    )

    missing_report_dates = sum(
        not observation.get("report_date")
        for observation in observations
    )

    missing_source_pages = sum(
        not observation.get("source", {}).get("page")
        for observation in observations
    )

    completeness = {
        "missing_project_names": missing_names,
        "missing_sectors": missing_sectors,
        "missing_report_dates": missing_report_dates,
        "missing_source_pages": missing_source_pages,
    }

    # ---------------------------------------------------------
    # Validity checks
    # ---------------------------------------------------------

    invalid_milestones = 0
    suspicious_milestone_records = []

    for observation in observations:
        achieved = observation.get("milestones_achieved")
        total = observation.get("milestones_total")

        if achieved is None or total is None:
            continue

        if achieved < 0 or total < 0 or achieved > total:
            invalid_milestones += 1

            suspicious_milestone_records.append(
                {
                    "serial_no": observation.get("serial_no"),
                    "project_name": observation.get("project_name"),
                    "achieved": achieved,
                    "total": total,
                }
            )

    validity_checks = {
        "milestones_valid": invalid_milestones == 0,
    }

    # ---------------------------------------------------------
    # Overall status
    #
    # Completeness does NOT determine PASS/WARN because
    # missing source values can be legitimate.
    # ---------------------------------------------------------

    status = (
        "PASS"
        if all(structural_checks.values())
        and all(validity_checks.values())
        else "WARN"
    )

    return {
        "status": status,

        "observations": len(observations),

        "serial_min": min_serial,
        "serial_max": max_serial,

        "missing_serials": missing_serials,
        "duplicate_serials": duplicate_serials,

        "structural_checks": structural_checks,

        "completeness": completeness,

        "validity": {
            "invalid_milestones": invalid_milestones,
            "suspicious_milestone_records": (
                suspicious_milestone_records
            ),
            "checks": validity_checks,
        },
    }


def build_dataset_qa(
    qa_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a dataset-level QA summary from report-level QA results."""

    total_reports = len(qa_summaries)

    passed_reports = sum(
        qa.get("status") == "PASS"
        for qa in qa_summaries
    )

    warned_reports = sum(
        qa.get("status") == "WARN"
        for qa in qa_summaries
    )

    total_observations = sum(
        qa.get("observations", 0)
        for qa in qa_summaries
    )

    total_missing_serials = sum(
        len(qa.get("missing_serials", []))
        for qa in qa_summaries
    )

    total_duplicate_serials = sum(
        len(qa.get("duplicate_serials", []))
        for qa in qa_summaries
    )

    total_invalid_milestones = sum(
        qa.get("validity", {})
        .get("invalid_milestones", 0)
        for qa in qa_summaries
    )

    total_missing_names = sum(
        qa.get("completeness", {})
        .get("missing_project_names", 0)
        for qa in qa_summaries
    )

    total_missing_sectors = sum(
        qa.get("completeness", {})
        .get("missing_sectors", 0)
        for qa in qa_summaries
    )

    total_missing_report_dates = sum(
        qa.get("completeness", {})
        .get("missing_report_dates", 0)
        for qa in qa_summaries
    )

    total_missing_source_pages = sum(
        qa.get("completeness", {})
        .get("missing_source_pages", 0)
        for qa in qa_summaries
    )

    return {
        "status": (
            "PASS"
            if warned_reports == 0
            else "WARN"
        ),

        "reports": {
            "total": total_reports,
            "passed": passed_reports,
            "warnings": warned_reports,
        },

        "observations": total_observations,

        "structural": {
            "missing_serials": total_missing_serials,
            "duplicate_serials": total_duplicate_serials,
        },

        "completeness": {
            "missing_project_names": total_missing_names,
            "missing_sectors": total_missing_sectors,
            "missing_report_dates": total_missing_report_dates,
            "missing_source_pages": total_missing_source_pages,
        },

        "validity": {
            "invalid_milestones": total_invalid_milestones,
        },

        "report_qa": qa_summaries,
    }
