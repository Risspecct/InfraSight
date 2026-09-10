from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import ProjectObservation


MODEL_FEATURES = [
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


def months_between(a: pd.Series, b: pd.Series) -> pd.Series:
    return (
        (a.dt.year - b.dt.year) * 12
        + (a.dt.month - b.dt.month)
    )


def build_features(
    db: Session,
    project_id: str,
    observation_id: str,
) -> pd.DataFrame:
    observations = db.scalars(
        select(ProjectObservation)
        .where(ProjectObservation.project_id == project_id)
        .order_by(
            ProjectObservation.report_date,
            ProjectObservation.observation_id,
        )
    ).all()

    if not observations:
        raise ValueError(
            f"No observations found for project {project_id}"
        )

    rows = [
        {
            "observation_id": o.observation_id,
            "project_id": o.project_id,
            "project_code": o.project_code,
            "project_name": o.project_name,
            "report_date": o.report_date,
            "approval_date": o.approval_date,
            "approval_date_revised": o.approval_date_revised,
            "original_cost_crore": o.original_cost_crore,
            "revised_cost_crore": o.revised_cost_crore,
            "anticipated_cost_crore": o.anticipated_cost_crore,
            "cumulative_expenditure_crore": o.cumulative_expenditure_crore,
            "original_completion_date": o.original_completion_date,
            "revised_completion_date": o.revised_completion_date,
            "anticipated_completion_date": o.anticipated_completion_date,
            "time_overrun_original_months": o.time_overrun_original_months,
            "time_overrun_revised_months": o.time_overrun_revised_months,
            "additional_delay_months": o.additional_delay_months,
            "milestones_achieved": o.milestones_achieved,
            "milestones_total": o.milestones_total,
        }
        for o in observations
    ]

    df = pd.DataFrame(rows)

    # Parse dates exactly as the training pipeline does.
    df["report_date"] = pd.to_datetime(
        df["report_date"],
        format="%Y-%m",
        errors="coerce",
    )

    for column in [
        "approval_date",
        "approval_date_revised",
        "original_completion_date",
        "revised_completion_date",
        "anticipated_completion_date",
    ]:
        df[f"{column}_parsed"] = pd.to_datetime(
            df[column],
            errors="coerce",
        )

    # The observations were already ordered by project/date.
    # Still explicitly sort to make this invariant clear.
    df = df.sort_values(
        ["report_date", "observation_id"]
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # Observation / project age features
    # ---------------------------------------------------------

    df["derived_observation_number"] = (
        np.arange(len(df)) + 1
    )

    first_report_date = df["report_date"].min()

    df["derived_months_since_first_report"] = (
        months_between(
            df["report_date"],
            pd.Series(
                [first_report_date] * len(df),
                index=df.index,
            ),
        )
    )

    df["derived_project_report_gap_months"] = (
        df["report_date"]
        .diff()
        .dt.days
        .div(30.4375)
    )

    df["derived_report_year"] = df["report_date"].dt.year
    df["derived_report_month"] = df["report_date"].dt.month

    df["derived_project_age_months"] = months_between(
        df["report_date"],
        df["approval_date_parsed"],
    )

    # ---------------------------------------------------------
    # Schedule features
    # ---------------------------------------------------------

    df["derived_months_to_original_completion"] = months_between(
        df["original_completion_date_parsed"],
        df["report_date"],
    )

    df["derived_months_to_anticipated_completion"] = months_between(
        df["anticipated_completion_date_parsed"],
        df["report_date"],
    )

    # ---------------------------------------------------------
    # Cost features
    # ---------------------------------------------------------

    def safe_ratio(
        numerator: pd.Series,
        denominator: pd.Series,
    ) -> pd.Series:
        return np.where(
            denominator.notna()
            & (denominator > 0)
            & numerator.notna(),
            numerator / denominator * 100,
            np.nan,
        )

    df["derived_expenditure_to_original_cost_pct"] = safe_ratio(
        df["cumulative_expenditure_crore"],
        df["original_cost_crore"],
    )

    df["derived_anticipated_cost_increase_pct"] = safe_ratio(
        df["anticipated_cost_crore"],
        df["original_cost_crore"],
    )

    df["derived_expenditure_to_anticipated_cost_pct"] = safe_ratio(
        df["cumulative_expenditure_crore"],
        df["anticipated_cost_crore"],
    )

    df["derived_cost_increase_crore"] = np.where(
        df["anticipated_cost_crore"].notna()
        & df["original_cost_crore"].notna(),
        df["anticipated_cost_crore"]
        - df["original_cost_crore"],
        np.nan,
    )

    # ---------------------------------------------------------
    # Milestone features
    # ---------------------------------------------------------

    df["derived_milestone_progress_pct"] = np.where(
        df["milestones_total"] > 0,
        df["milestones_achieved"]
        / df["milestones_total"]
        * 100,
        np.nan,
    )

    df["derived_milestone_gap"] = (
        df["milestones_total"]
        - df["milestones_achieved"]
    )

    df["derived_milestone_inconsistency"] = (
        df["milestones_achieved"]
        > df["milestones_total"]
    ).astype("int8")

    # ---------------------------------------------------------
    # Presence indicators
    # ---------------------------------------------------------

    for column in [
        "cumulative_expenditure_crore",
        "anticipated_cost_crore",
        "original_completion_date",
        "anticipated_completion_date",
        "time_overrun_original_months",
        "additional_delay_months",
    ]:
        df[f"derived_has_{column}"] = (
            df[column].notna().astype("int8")
        )

    # ---------------------------------------------------------
    # Strictly backward-looking deltas
    # ---------------------------------------------------------

    for column in [
        "anticipated_cost_crore",
        "cumulative_expenditure_crore",
        "time_overrun_original_months",
        "derived_milestone_progress_pct",
        "derived_months_to_anticipated_completion",
    ]:
        df[f"derived_delta_{column}"] = df[column].diff()

    previous_anticipated_cost = (
        df["anticipated_cost_crore"].shift(1)
    )

    df["derived_anticipated_cost_change_pct"] = np.where(
        (previous_anticipated_cost > 0)
        & df["anticipated_cost_crore"].notna(),
        (
            df["anticipated_cost_crore"]
            / previous_anticipated_cost
            - 1
        )
        * 100,
        np.nan,
    )

    previous_expenditure = (
        df["cumulative_expenditure_crore"].shift(1)
    )

    df["derived_expenditure_change_pct"] = np.where(
        (previous_expenditure > 0)
        & df["cumulative_expenditure_crore"].notna(),
        (
            df["cumulative_expenditure_crore"]
            / previous_expenditure
            - 1
        )
        * 100,
        np.nan,
    )

    # ---------------------------------------------------------
    # 3-observation backward-looking rolling features
    # ---------------------------------------------------------

    df["derived_3obs_cost_change_mean"] = (
        df["derived_anticipated_cost_change_pct"]
        .rolling(3, min_periods=2)
        .mean()
    )

    df["derived_3obs_expenditure_change_mean"] = (
        df["derived_expenditure_change_pct"]
        .rolling(3, min_periods=2)
        .mean()
    )

    df["derived_3obs_time_overrun_delta_mean"] = (
        df["derived_delta_time_overrun_original_months"]
        .rolling(3, min_periods=2)
        .mean()
    )

    df["derived_3obs_milestone_progress_delta_mean"] = (
        df["derived_delta_derived_milestone_progress_pct"]
        .rolling(3, min_periods=2)
        .mean()
    )

    # ---------------------------------------------------------
    # Current risk signals
    # ---------------------------------------------------------

    df["derived_reported_time_overrun_flag"] = (
        (
            df["time_overrun_original_months"]
            .fillna(0)
            > 0
        )
        | (
            df["additional_delay_months"]
            .fillna(0)
            > 0
        )
    ).astype("int8")

    df["derived_cost_escalation_flag_10pct"] = (
        df["derived_anticipated_cost_increase_pct"] >= 10
    ).astype("int8")

    df["derived_low_milestone_progress_flag"] = (
        (df["derived_project_age_months"] >= 12)
        & df["derived_milestone_progress_pct"].notna()
        & (df["derived_milestone_progress_pct"] < 50)
    ).astype("int8")

    # ---------------------------------------------------------
    # Select requested observation
    # ---------------------------------------------------------

    target_rows = df[
        df["observation_id"] == observation_id
    ]

    if target_rows.empty:
        raise ValueError(
            f"Observation {observation_id} "
            f"not found for project {project_id}"
        )

    row = target_rows.iloc[0]

    # Preserve the exact model column order.
    features = pd.DataFrame(
        [[row.get(column, np.nan) for column in MODEL_FEATURES]],
        columns=MODEL_FEATURES,
    )

    return features
