from pydantic import BaseModel, Field


class RiskComponent(BaseModel):
    probability: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    flagged: bool


class DecisionInput(BaseModel):
    project_id: str
    prediction_date: str

    cost_probability: float = Field(ge=0.0, le=1.0)
    schedule_probability: float = Field(ge=0.0, le=1.0)


class DecisionResult(BaseModel):
    project_id: str
    prediction_date: str

    cost_risk: RiskComponent
    schedule_risk: RiskComponent

    risk_level: str
    priority_score: float = Field(ge=0.0, le=100.0)
    early_warning: bool
