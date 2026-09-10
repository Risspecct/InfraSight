from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Project, ProjectObservation


def build_project_evidence(
    db: Session,
    project_id: str,
    observation_id: str,
) -> dict:

    project = db.get(Project, project_id)

    if project is None:
        raise ValueError("Project not found")

    # ---------------------------------------------------------
    # 1. Find the selected observation
    # ---------------------------------------------------------
    current = db.scalar(
        select(ProjectObservation)
        .where(
            ProjectObservation.project_id == project_id,
            ProjectObservation.observation_id == observation_id,
        )
    )

    if current is None:
        raise ValueError("Observation not found")

    # ---------------------------------------------------------
    # 2. Retrieve only observations known at that point in time
    # ---------------------------------------------------------
    observations = db.scalars(
        select(ProjectObservation)
        .where(
            ProjectObservation.project_id == project_id,
            ProjectObservation.report_date <= current.report_date,
        )
        .order_by(
            ProjectObservation.report_date.asc(),
            ProjectObservation.observation_id.asc(),
        )
    ).all()

    history = []

    for obs in observations:
        history.append(
            {
                "observation_id": obs.observation_id,
                "report_date": obs.report_date,

                "anticipated_cost_crore":
                    obs.anticipated_cost_crore,

                "revised_cost_crore":
                    obs.revised_cost_crore,

                "cumulative_expenditure_crore":
                    obs.cumulative_expenditure_crore,

                "anticipated_completion_date":
                    obs.anticipated_completion_date,

                "time_overrun_original_months":
                    obs.time_overrun_original_months,

                "additional_delay_months":
                    obs.additional_delay_months,

                "milestones_achieved":
                    obs.milestones_achieved,

                "milestones_total":
                    obs.milestones_total,

                "physical_progress_pct":
                    obs.physical_progress_pct,

                "delay_reason":
                    obs.delay_reason,

                "status":
                    obs.status,

                "source_report":
                    obs.source_report,

                "source_page":
                    obs.source_page,
            }
        )

    # ---------------------------------------------------------
    # 3. Return only metadata that is valid as of the
    #    selected observation
    # ---------------------------------------------------------
    return {
        "project": {
            "project_id": project.project_id,
            "name": project.canonical_project_name,
            "agency": project.canonical_agency,
            "state": project.canonical_state,
            "sector": project.canonical_sector,
            "first_report_date": project.first_report_date,
            "last_report_date": current.report_date,
        },

        "current_observation": next(
            item
            for item in history
            if item["observation_id"] == observation_id
        ),

        "historical_observations": history,
    }
