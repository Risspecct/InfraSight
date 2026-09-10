from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import ProjectObservation
from app.decision.engine import evaluate_decision
from app.decision.schemas import DecisionInput
from app.services.inference import predict_project


def assess_project(
    db: Session,
    project_id: str,
    observation_id: str,
) -> dict:
    observation = db.scalar(
        select(ProjectObservation)
        .where(
            ProjectObservation.project_id == project_id,
            ProjectObservation.observation_id == observation_id,
        )
    )

    if observation is None:
        raise ValueError("Observation not found")

    prediction = predict_project(
        db,
        project_id,
        observation_id,
    )

    decision = evaluate_decision(
        DecisionInput(
            project_id=project_id,
            prediction_date=observation.report_date,
            cost_probability=prediction[
                "cost_overrun_probability"
            ],
            schedule_probability=prediction[
                "schedule_overrun_probability"
            ],
        )
    )

    return {
        "project_id": project_id,
        "observation_id": observation_id,
        "prediction_date": observation.report_date,
        "cost_overrun_probability": prediction[
            "cost_overrun_probability"
        ],
        "schedule_overrun_probability": prediction[
            "schedule_overrun_probability"
        ],
        "cost_risk": decision.cost_risk,
        "schedule_risk": decision.schedule_risk,
        "risk_level": decision.risk_level,
        "priority_score": decision.priority_score,
        "early_warning": decision.early_warning,
    }