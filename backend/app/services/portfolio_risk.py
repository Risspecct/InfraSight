from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Project
from app.decision.engine import (
    calculate_priority_score,
    determine_risk_level,
)
from app.decision.rules import (
    is_cost_flagged,
    is_schedule_flagged,
)
from app.services.feature_builder import build_portfolio_features
from app.services.model_loader import (
    load_cost_model,
    load_schedule_model,
)


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

    project_names = {
        project.project_id: project.canonical_project_name
        for project in projects
    }

    features = build_portfolio_features(db)

    if features.empty:
        return {
            "items": [],
            "page": page,
            "page_size": page_size,
            "total": 0,
            "total_pages": 0,
        }

    metadata = features[
        [
            "project_id",
            "observation_id",
            "project_name",
            "report_date",
        ]
    ].copy()

    model_features = features.drop(
        columns=[
            "project_id",
            "observation_id",
            "project_name",
            "report_date",
        ]
    )

    cost_model = load_cost_model()
    schedule_bundle = load_schedule_model()
    schedule_model = schedule_bundle["model"]

    cost_probabilities = cost_model.predict(
        model_features
    )

    schedule_probabilities = (
        schedule_model.predict_proba(
            model_features
        )[:, 1]
    )

    assessments = []

    for index, row in metadata.iterrows():
        cost_probability = float(
            cost_probabilities[index]
        )

        schedule_probability = float(
            schedule_probabilities[index]
        )

        cost_flagged = is_cost_flagged(
            cost_probability
        )

        schedule_flagged = is_schedule_flagged(
            schedule_probability
        )

        risk_level = determine_risk_level(
            cost_flagged,
            schedule_flagged,
        )

        priority_score = calculate_priority_score(
            cost_probability,
            schedule_probability,
        )

        assessments.append(
            {
                "project_id": row["project_id"],
                "project_name": project_names.get(
                    row["project_id"],
                    row["project_name"],
                ),
                "assessment_date": row["report_date"],
                "observation_id": row["observation_id"],
                "cost_probability": cost_probability,
                "schedule_probability": schedule_probability,
                "risk_level": risk_level,
                "priority_score": priority_score,
                "early_warning": (
                    risk_level in {"HIGH", "CRITICAL"}
                ),
            }
        )

        assessments.sort(
            key=lambda item: item["priority_score"],
            reverse=True,
        )
    
        total = len(assessments)
    
    return {
        "items": assessments,
        "page": 1,
        "page_size": total,
        "total": total,
        "total_pages": 1,
    }
