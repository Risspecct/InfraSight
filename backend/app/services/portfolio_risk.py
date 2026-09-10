from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Project, ProjectObservation
from app.services.risk_assessment import assess_project


def _get_latest_observation(
    db: Session,
    project_id: str,
) -> ProjectObservation | None:
    return db.scalars(
        select(ProjectObservation)
        .where(
            ProjectObservation.project_id == project_id
        )
        .order_by(
            ProjectObservation.report_date.desc(),
            ProjectObservation.observation_id.desc(),
        )
        .limit(1)
    ).first()


def get_portfolio_risk(
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    projects = db.scalars(
        select(Project).order_by(
            Project.canonical_project_name
        )
    ).all()

    assessments = []

    for project in projects:
        observation = _get_latest_observation(
            db,
            project.project_id,
        )

        if observation is None:
            continue

        assessment = assess_project(
            db,
            project.project_id,
            observation.observation_id,
        )

        assessments.append(
            {
                "project_id": project.project_id,
                "project_name": project.canonical_project_name,
                "assessment_date": assessment["prediction_date"],
                "observation_id": assessment["observation_id"],
                "cost_probability": assessment[
                    "cost_overrun_probability"
                ],
                "schedule_probability": assessment[
                    "schedule_overrun_probability"
                ],
                "risk_level": assessment["risk_level"],
                "priority_score": assessment["priority_score"],
                "early_warning": assessment["early_warning"],
            }
        )

    assessments.sort(
        key=lambda item: item["priority_score"],
        reverse=True,
    )

    total = len(assessments)

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": assessments[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (
            total + page_size - 1
        ) // page_size,
    }
