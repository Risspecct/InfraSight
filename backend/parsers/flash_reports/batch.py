from __future__ import annotations

from pathlib import Path
import json

from .common import (
    build_dataset_qa,
    build_qa_summary,
    create_output_directory,
    infer_report_date,
    write_outputs,
)
from .registry import detect_format, get_parser


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "processed"


def main() -> None:
    print("=" * 60)
    print("FLASH REPORT BATCH PARSER")
    print("=" * 60)
    print()

    RAW_DIRECTORY.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(RAW_DIRECTORY.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in: {RAW_DIRECTORY}")
        return

    # ---------------------------------------------------------
    # Determine which reports are new
    # ---------------------------------------------------------

    files_to_process = []
    skipped = []

    for pdf_path in pdf_files:
        output_directory = OUTPUT_DIRECTORY / pdf_path.stem
        observations_path = output_directory / "observations.json"

        if observations_path.exists():
            skipped.append(pdf_path)
        else:
            files_to_process.append(pdf_path)

    print(f"Reports discovered : {len(pdf_files)}")
    print(f"Already processed  : {len(skipped)}")
    print(f"New reports        : {len(files_to_process)}")
    print()

    if skipped:
        print("Skipped reports:")
        for pdf_path in skipped:
            print(f"  [SKIP] {pdf_path.name}")
        print()

    successful = []
    failed = []

    total_observations = 0

    # ---------------------------------------------------------
    # Parse only new reports
    # ---------------------------------------------------------

    for pdf_path in files_to_process:
        try:
            report_date = infer_report_date(pdf_path)
            format_name = detect_format(report_date)
            parser = get_parser(format_name)

            observations = parser.parse(
                pdf_path,
                report_date,
            )

            output_directory = create_output_directory(
                OUTPUT_DIRECTORY,
                pdf_path,
            )

            json_path, csv_path = write_outputs(
                observations,
                output_directory,
            )

            qa_summary = build_qa_summary(observations)

            qa_summary["report"] = pdf_path.name
            qa_summary["report_date"] = report_date
            qa_summary["format"] = format_name

            qa_path = output_directory / "qa.json"

            qa_path.write_text(
                json.dumps(
                    qa_summary,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            print(
                f"[{'PASS' if qa_summary['status'] == 'PASS' else 'WARN'}] "
                f"{pdf_path.name}: "
                f"{len(observations)} observations | "
                f"serials "
                f"{qa_summary['serial_min']}-"
                f"{qa_summary['serial_max']} | "
                f"missing "
                f"{len(qa_summary['missing_serials'])} | "
                f"duplicates "
                f"{len(qa_summary['duplicate_serials'])}"
            )

            successful.append(
                {
                    "file": pdf_path.name,
                    "report_date": report_date,
                    "format": format_name,
                    "observations": len(observations),
                    "json": json_path,
                    "csv": csv_path,
                }
            )

            total_observations += len(observations)

            print(
                f"[PASS] {pdf_path.name:<35} "
                f"{len(observations):>4} observations"
            )

        except Exception as exc:
            failed.append(
                {
                    "file": pdf_path.name,
                    "error": str(exc),
                }
            )

            print(
                f"[FAIL] {pdf_path.name:<35} "
                f"{exc}"
            )

    # ---------------------------------------------------------
    # Aggregate QA across ALL processed reports
    # ---------------------------------------------------------

    qa_summaries = []

    for report_directory in sorted(OUTPUT_DIRECTORY.iterdir()):
        if not report_directory.is_dir():
            continue

        qa_path = report_directory / "qa.json"

        if not qa_path.exists():
            continue

        try:
            qa_summary = json.loads(
                qa_path.read_text(
                    encoding="utf-8",
                )
            )

            qa_summaries.append(qa_summary)

        except (json.JSONDecodeError, OSError) as exc:
            print(
                f"[WARN] Could not read QA file: "
                f"{qa_path}: {exc}"
            )

    dataset_qa = build_dataset_qa(
        qa_summaries
    )

    dataset_qa_path = OUTPUT_DIRECTORY / "dataset_qa.json"

    dataset_qa_path.write_text(
        json.dumps(
            dataset_qa,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print()
    print("-" * 60)
    print("SUMMARY")
    print("-" * 60)

    print(f"Reports discovered : {len(pdf_files)}")
    print(f"Already processed  : {len(skipped)}")
    print(f"New reports        : {len(files_to_process)}")
    print(f"Reports processed  : {len(successful)}")
    print(f"Reports failed     : {len(failed)}")

    print(
        f"New observations   : {total_observations}"
    )

    print(
        f"Dataset QA status  : {dataset_qa['status']}"
    )

    print(
        f"Dataset reports    : "
        f"{dataset_qa['reports']['total']}"
    )

    print(
        f"Dataset observations: "
        f"{dataset_qa['observations']}"
    )

    print()

    # ---------------------------------------------------------
    # Newly processed reports
    # ---------------------------------------------------------

    if successful:
        print("Newly processed reports:")
        print(
            f"{'REPORT':<35} "
            f"{'DATE':<10} "
            f"{'FORMAT':<15} "
            f"{'PROJECTS':>8}"
        )
        print("-" * 75)

        for result in successful:
            print(
                f"{result['file']:<35} "
                f"{result['report_date']:<10} "
                f"{result['format']:<15} "
                f"{result['observations']:>8}"
            )

    # ---------------------------------------------------------
    # Failed reports
    # ---------------------------------------------------------

    if failed:
        print()
        print("Failed reports:")
        print(
            f"{'REPORT':<35} ERROR"
        )
        print("-" * 75)

        for result in failed:
            print(
                f"{result['file']:<35} "
                f"{result['error']}"
            )

    print()
    print(
        f"Dataset QA: {OUTPUT_DIRECTORY / 'dataset_qa.json'}"
    )
    print(
        f"Output directory: {OUTPUT_DIRECTORY}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
