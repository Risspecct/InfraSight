from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.feature_builder import build_features
from app.services.model_loader import load_cost_model, load_schedule_model


def predict_project(
    db: Session,
    project_id: str,
    observation_id: str,
) -> dict[str, float | str]:
    features = build_features(
        db,
        project_id,
        observation_id,
    )

    cost_model = load_cost_model()
    schedule_bundle = load_schedule_model()

    cost_probability = float(
        cost_model.predict(features)[0]
    )

    schedule_model = schedule_bundle["model"]

    schedule_probability = float(
        schedule_model.predict_proba(features)[0][1]
    )

    return {
        "project_id": project_id,
        "observation_id": observation_id,
        "cost_overrun_probability": cost_probability,
        "schedule_overrun_probability": schedule_probability,
    }
