COST_RISK_THRESHOLD = 0.48869
SCHEDULE_RISK_THRESHOLD = 0.49592


def is_cost_flagged(probability: float) -> bool:
    return probability >= COST_RISK_THRESHOLD


def is_schedule_flagged(probability: float) -> bool:
    return probability >= SCHEDULE_RISK_THRESHOLD
