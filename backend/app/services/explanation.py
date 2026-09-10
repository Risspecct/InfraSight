from __future__ import annotations

import pandas as pd
import shap
from sqlalchemy.orm import Session

from app.services.feature_builder import build_features
from app.services.model_loader import load_cost_model, load_schedule_model


FEATURE_LABELS = {
    "original_cost_crore": "Original project cost",
    "anticipated_cost_crore": "Anticipated project cost",
    "cumulative_expenditure_crore": "Cumulative expenditure",
    "derived_observation_number": "Observation number",
    "derived_months_since_first_report": "Months since first report",
    "derived_project_report_gap_months": "Reporting interval",
    "derived_report_year": "Report year",
    "derived_report_month": "Report month",
    "derived_project_age_months": "Project age",
    "derived_months_to_original_completion": "Months to original completion",
    "derived_months_to_anticipated_completion": "Months to anticipated completion",
    "derived_expenditure_to_original_cost_pct": "Expenditure relative to original cost",
    "derived_expenditure_to_anticipated_cost_pct": "Expenditure relative to anticipated cost",
    "derived_anticipated_cost_increase_pct": "Anticipated cost relative to original cost",
    "derived_cost_increase_crore": "Anticipated cost increase",
    "derived_milestone_progress_pct": "Milestone progress",
    "derived_milestone_gap": "Remaining milestones",
    "derived_milestone_inconsistency": "Milestone inconsistency",
    "derived_has_cumulative_expenditure_crore": "Expenditure data available",
    "derived_has_anticipated_cost_crore": "Anticipated cost available",
    "derived_has_original_completion_date": "Original completion date available",
    "derived_has_anticipated_completion_date": "Anticipated completion date available",
    "derived_has_time_overrun_original_months": "Original time-overrun data available",
    "derived_has_additional_delay_months": "Additional delay data available",
    "derived_delta_anticipated_cost_crore": "Change in anticipated cost",
    "derived_delta_cumulative_expenditure_crore": "Change in expenditure",
    "derived_delta_time_overrun_original_months": "Change in original time overrun",
    "derived_delta_derived_milestone_progress_pct": "Change in milestone progress",
    "derived_delta_derived_months_to_anticipated_completion": "Change in anticipated completion horizon",
    "derived_anticipated_cost_change_pct": "Anticipated cost change",
    "derived_expenditure_change_pct": "Expenditure change",
    "derived_3obs_cost_change_mean": "Recent cost-change trend",
    "derived_3obs_expenditure_change_mean": "Recent expenditure trend",
    "derived_3obs_time_overrun_delta_mean": "Recent delay trend",
    "derived_3obs_milestone_progress_delta_mean": "Recent milestone-progress trend",
    "derived_reported_time_overrun_flag": "Reported time overrun",
    "derived_cost_escalation_flag_10pct": "Cost escalation flag",
    "derived_low_milestone_progress_flag": "Low milestone progress flag",
}


def _normalise_shap_values(values):
    """Return a single 2D SHAP array regardless of SHAP output format."""
    if isinstance(values, list):
        # Binary classifiers can return one array per class.
        values = values[-1]

    values = getattr(values, "values", values)

    if hasattr(values, "ndim") and values.ndim == 3:
        values = values[:, :, -1]

    return values


def _build_drivers(
    model,
    features: pd.DataFrame,
    top_k: int = 5,
) -> list[dict]:
    explainer = shap.TreeExplainer(model)
    shap_values = _normalise_shap_values(explainer.shap_values(features))

    row_values = shap_values[0]

    drivers = []

    for feature, value, contribution in zip(
        features.columns,
        features.iloc[0].tolist(),
        row_values.tolist(),
    ):
        contribution = float(contribution)

        drivers.append(
            {
                "feature": feature,
                "label": FEATURE_LABELS.get(feature, feature),
                "value": None if pd.isna(value) else float(value),
                "shap_value": contribution,
                "direction": (
                    "increases_risk"
                    if contribution > 0
                    else "decreases_risk"
                    if contribution < 0
                    else "neutral"
                ),
            }
        )

    # Largest absolute contributions first.
    drivers.sort(
        key=lambda item: abs(item["shap_value"]),
        reverse=True,
    )

    return drivers[:top_k]


def explain_project(
    db: Session,
    project_id: str,
    observation_id: str,
    top_k: int = 5,
) -> dict:
    features = build_features(
        db,
        project_id,
        observation_id,
    )

    cost_model = load_cost_model()
    schedule_bundle = load_schedule_model()
    schedule_model = schedule_bundle["model"]

    return {
        "project_id": project_id,
        "observation_id": observation_id,
        "cost_drivers": _build_drivers(
            cost_model,
            features,
            top_k,
        ),
        "schedule_drivers": _build_drivers(
            schedule_model,
            features,
            top_k,
        ),
    }
