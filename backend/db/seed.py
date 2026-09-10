from pathlib import Path

import pandas as pd
from sqlalchemy import delete

from db.database import SessionLocal
from db.models import Project, ProjectObservation


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

PROJECTS_FILE = DATA_DIR / "project_master.csv"
OBSERVATIONS_FILE = DATA_DIR / "project_observations.csv"

BATCH_SIZE = 1000


def seed_projects(session):
    print("Loading project_master.csv...")

    df = pd.read_csv(PROJECTS_FILE)

    records = df.to_dict(orient="records")

    projects = [
        Project(
            project_id=row["project_id"],
            canonical_project_code=row.get("canonical_project_code"),
            canonical_project_name=row["canonical_project_name"],
            canonical_agency=row.get("canonical_agency"),
            canonical_state=row.get("canonical_state"),
            canonical_sector=row.get("canonical_sector"),
            first_report_date=row["first_report_date"],
            last_report_date=row["last_report_date"],
            observation_count=int(row["observation_count"]),
            identity_confidence=row["identity_confidence"],
        )
        for row in records
    ]

    for start in range(0, len(projects), BATCH_SIZE):
        session.add_all(projects[start:start + BATCH_SIZE])
        session.flush()

    print(f"Projects loaded: {len(projects):,}")


def seed_observations(session):
    print("Loading project_observations.csv...")

    df = pd.read_csv(OBSERVATIONS_FILE)

    # Convert pandas NaN values to Python None so PostgreSQL receives NULL.
    df = df.where(pd.notna(df), None)

    records = df.to_dict(orient="records")

    observations = []

    for row in records:
        observations.append(
            ProjectObservation(
                observation_id=row["observation_id"],
                project_id=row["project_id"],
                project_code=row["project_code"],
                serial_no=(
                    int(row["serial_no"])
                    if row["serial_no"] is not None
                    else None
                ),
                project_name=row["project_name"],
                agency=row["agency"],
                state=row["state"],
                sector=row["sector"],
                report_date=row["report_date"],
                approval_date=row["approval_date"],
                approval_date_revised=row["approval_date_revised"],
                original_cost_crore=row["original_cost_crore"],
                revised_cost_crore=row["revised_cost_crore"],
                anticipated_cost_crore=row["anticipated_cost_crore"],
                cost_overrun_original_crore=row["cost_overrun_original_crore"],
                cost_overrun_revised_crore=row["cost_overrun_revised_crore"],
                cumulative_expenditure_crore=row["cumulative_expenditure_crore"],
                original_completion_date=row["original_completion_date"],
                revised_completion_date=row["revised_completion_date"],
                anticipated_completion_date=row["anticipated_completion_date"],
                time_overrun_original_months=row["time_overrun_original_months"],
                time_overrun_revised_months=row["time_overrun_revised_months"],
                additional_delay_months=row["additional_delay_months"],
                milestones_achieved=int(row["milestones_achieved"]),
                milestones_total=int(row["milestones_total"]),
                physical_progress_pct=row["physical_progress_pct"],
                delay_reason=row["delay_reason"],
                status=row["status"],
                source_report=row["source_report"],
                source_table=row["source_table"],
                source_page=int(row["source_page"]),
                source_serial_no=int(row["source_serial_no"]),
            )
        )

        if len(observations) >= BATCH_SIZE:
            session.add_all(observations)
            session.flush()
            print(f"  Loaded {len(observations):,} observations...")
            observations.clear()

    if observations:
        session.add_all(observations)
        session.flush()

    print(f"Observations loaded: {len(records):,}")


def main():
    if not PROJECTS_FILE.exists():
        raise FileNotFoundError(
            f"Missing file: {PROJECTS_FILE}"
        )

    if not OBSERVATIONS_FILE.exists():
        raise FileNotFoundError(
            f"Missing file: {OBSERVATIONS_FILE}"
        )

    session = SessionLocal()

    try:
        print("=" * 60)
        print("InfraSight database seed")
        print("=" * 60)

        # Make the script safely re-runnable.
        print("Clearing existing application data...")
        session.execute(delete(ProjectObservation))
        session.execute(delete(Project))
        session.commit()

        seed_projects(session)
        session.commit()

        seed_observations(session)
        session.commit()

        print("=" * 60)
        print("Database seed completed successfully.")
        print("=" * 60)

    except Exception:
        session.rollback()
        print("Seed failed. Transaction rolled back.")
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
