from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import ProjectObservation
from app.services.inference import predict_project


BACKTEST_HORIZON = 3
COST_DETERIORATION_THRESHOLD = 0.10
SCHEDULE_DETERIORATION_THRESHOLD_MONTHS = 3.0


def _future_observations(
    db: Session,
    project_id: str,
    observation: ProjectObservation,
) -> list[ProjectObservation]:
    observations = db.scalars(
        select(ProjectObservation)
        .where(
            ProjectObservation.project_id == project_id,
            ProjectObservation.report_date > observation.report_date,
        )
        .order_by(ProjectObservation.report_date)
        .limit(BACKTEST_HORIZON)
    ).all()

    return observations


def _actual_cost_deterioration(
    observation: ProjectObservation,
    future_observations: list[ProjectObservation],
) -> bool | None:
    current_cost = observation.anticipated_cost_crore

    if current_cost is None or current_cost <= 0:
        return None

    future_costs = [
        item.anticipated_cost_crore
        for item in future_observations
        if item.anticipated_cost_crore is not None
    ]

    if not future_costs:
        return None

    return max(future_costs) >= (
        current_cost * (1 + COST_DETERIORATION_THRESHOLD)
    )


def _actual_schedule_deterioration(
    observation: ProjectObservation,
    future_observations: list[ProjectObservation],
) -> bool | None:
    current_delay = observation.time_overrun_original_months

    if current_delay is None:
        return None

    future_delays = [
        item.time_overrun_original_months
        for item in future_observations
        if item.time_overrun_original_months is not None
    ]

    if not future_delays:
        return None

    return max(future_delays) >= (
        current_delay + SCHEDULE_DETERIORATION_THRESHOLD_MONTHS
    )


def backtest_project(
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
        raise ValueError("Observation not found for project")

    future_observations = _future_observations(
        db,
        project_id,
        observation,
    )

    prediction = predict_project(
        db,
        project_id,
        observation_id,
    )

    actual_cost = _actual_cost_deterioration(
        observation,
        future_observations,
    )

    actual_schedule = _actual_schedule_deterioration(
        observation,
        future_observations,
    )

    return {
        "project_id": project_id,
        "observation_id": observation_id,
        "prediction_date": observation.report_date,
        "horizon_observations": len(future_observations),
        "horizon_complete": len(future_observations) == BACKTEST_HORIZON,

        "predicted": {
            "cost_probability": prediction[
                "cost_overrun_probability"
            ],
            "schedule_probability": prediction[
                "schedule_overrun_probability"
            ],
        },

        "actual": {
            "cost_deterioration": actual_cost,
            "schedule_deterioration": actual_schedule,
        },

        "future_observation_ids": [
            item.observation_id
            for item in future_observations
        ],
    }
