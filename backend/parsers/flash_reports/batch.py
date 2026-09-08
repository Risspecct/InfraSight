from __future__ import annotations

from pathlib import Path

from .common import (
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

    successful = []
    failed = []

    total_observations = 0

    for pdf_path in pdf_files:
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

    print()
    print("-" * 60)
    print("SUMMARY")
    print("-" * 60)

    print(f"Reports discovered : {len(pdf_files)}")
    print(f"Reports processed  : {len(successful)}")
    print(f"Reports failed     : {len(failed)}")
    print(f"Total observations : {total_observations}")

    if successful:
        print()
        print("Successful reports:")
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
    print(f"Output directory: {OUTPUT_DIRECTORY}")
    print("=" * 60)


if __name__ == "__main__":
    main()
