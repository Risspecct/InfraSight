from typing import Any

import pandas as pd

from app.services.model_loader import load_cost_model, load_schedule_model


COST_FEATURES = [
    "original_cost_crore",
    "anticipated_cost_crore",
    "cumulative_expenditure_crore",
    "derived_observation_number",
    "derived_months_since_first_report",
    "derived_project_report_gap_months",
    "derived_report_year",
    "derived_report_month",
    "derived_project_age_months",
    "derived_months_to_original_completion",
    "derived_months_to_anticipated_completion",
    "derived_expenditure_to_original_cost_pct",
    "derived_expenditure_to_anticipated_cost_pct",
    "derived_anticipated_cost_increase_pct",
    "derived_cost_increase_crore",
    "derived_milestone_progress_pct",
    "derived_milestone_gap",
    "derived_milestone_inconsistency",
    "derived_has_cumulative_expenditure_crore",
    "derived_has_anticipated_cost_crore",
    "derived_has_original_completion_date",
    "derived_has_anticipated_completion_date",
    "derived_has_time_overrun_original_months",
    "derived_has_additional_delay_months",
    "derived_delta_anticipated_cost_crore",
    "derived_delta_cumulative_expenditure_crore",
    "derived_delta_time_overrun_original_months",
    "derived_delta_derived_milestone_progress_pct",
    "derived_delta_derived_months_to_anticipated_completion",
    "derived_anticipated_cost_change_pct",
    "derived_expenditure_change_pct",
    "derived_3obs_cost_change_mean",
    "derived_3obs_expenditure_change_mean",
    "derived_3obs_time_overrun_delta_mean",
    "derived_3obs_milestone_progress_delta_mean",
    "derived_reported_time_overrun_flag",
    "derived_cost_escalation_flag_10pct",
    "derived_low_milestone_progress_flag",
]


def predict(features: dict[str, Any]) -> dict[str, float]:
    missing = [
        feature
        for feature in COST_FEATURES
        if feature not in features
    ]

    if missing:
        raise ValueError(
            f"Missing model features: {missing}"
        )

    row = {
        feature: features[feature]
        for feature in COST_FEATURES
    }

    frame = pd.DataFrame([row], columns=COST_FEATURES)

    cost_model = load_cost_model()
    schedule_model = load_schedule_model()

    cost_probability = float(
        cost_model.predict(frame)[0]
    )

    schedule_probability = float(
        schedule_model["model"].predict_proba(frame)[0][1]
    )

    return {
        "cost_overrun_probability": cost_probability,
        "schedule_overrun_probability": schedule_probability,
    }
