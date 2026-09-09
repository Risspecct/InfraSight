from .rules import (
    is_cost_flagged,
    is_schedule_flagged,
    COST_RISK_THRESHOLD,
    SCHEDULE_RISK_THRESHOLD,
)
from .schemas import DecisionInput, DecisionResult, RiskComponent


def calculate_priority_score(
    cost_probability: float,
    schedule_probability: float,
) -> float:
    """
    Calculate the initial portfolio priority score.

    This v1 score reflects model risk only.
    Severity and trajectory modifiers will be added
    once the normalized project snapshots are available.
    """

    score = (
        0.5 * cost_probability
        + 0.5 * schedule_probability
    ) * 100

    return round(score, 2)


def determine_risk_level(
    cost_flagged: bool,
    schedule_flagged: bool,
) -> str:

    if cost_flagged and schedule_flagged:
        return "CRITICAL"

    if cost_flagged or schedule_flagged:
        return "HIGH"

    return "LOW"


def evaluate_decision(data: DecisionInput) -> DecisionResult:

    cost_flagged = is_cost_flagged(data.cost_probability)
    schedule_flagged = is_schedule_flagged(data.schedule_probability)

    risk_level = determine_risk_level(
        cost_flagged,
        schedule_flagged,
    )

    priority_score = calculate_priority_score(
        data.cost_probability,
        data.schedule_probability,
    )

    return DecisionResult(
        project_id=data.project_id,
        prediction_date=data.prediction_date,

        cost_risk=RiskComponent(
            probability=data.cost_probability,
            threshold=COST_RISK_THRESHOLD,
            flagged=cost_flagged,
        ),

        schedule_risk=RiskComponent(
            probability=data.schedule_probability,
            threshold=SCHEDULE_RISK_THRESHOLD,
            flagged=schedule_flagged,
        ),

        risk_level=risk_level,

        priority_score=priority_score,

        early_warning=risk_level in {"HIGH", "CRITICAL"},
    )
