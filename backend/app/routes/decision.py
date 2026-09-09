from fastapi import APIRouter

from app.decision.engine import evaluate_decision
from app.decision.schemas import DecisionInput, DecisionResult


router = APIRouter(
    prefix="/decision",
    tags=["Decision Engine"],
)


@router.post("/evaluate", response_model=DecisionResult)
def evaluate_project_decision(data: DecisionInput) -> DecisionResult:
    return evaluate_decision(data)
