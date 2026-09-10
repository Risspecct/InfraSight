from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Project, ProjectObservation
from app.services.risk_assessment import assess_project


def get_risk_trajectory(
    db: Session,
    project_id: str,
) -> dict:
    project = db.get(Project, project_id)

    if project is None:
        raise ValueError("Project not found")

    observations = db.scalars(
        select(ProjectObservation)
        .where(
            ProjectObservation.project_id == project_id
        )
        .order_by(
            ProjectObservation.report_date,
            ProjectObservation.observation_id,
        )
    ).all()

    trajectory = []

    for observation in observations:
        assessment = assess_project(
            db,
            project_id,
            observation.observation_id,
        )

        trajectory.append(
            {
                "observation_id": assessment["observation_id"],
                "assessment_date": assessment["prediction_date"],
                "cost_probability": assessment[
                    "cost_overrun_probability"
                ],
                "schedule_probability": assessment[
                    "schedule_overrun_probability"
                ],
                "risk_level": assessment["risk_level"],
                "priority_score": assessment[
                    "priority_score"
                ],
                "early_warning": assessment[
                    "early_warning"
                ],
            }
        )

    return {
        "project_id": project_id,
        "project_name": project.canonical_project_name,
        "observation_count": len(trajectory),
        "trajectory": trajectory,
    }
