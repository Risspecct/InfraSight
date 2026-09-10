from pydantic import BaseModel, Field


class IntelligenceRequest(BaseModel):
    observation_id: str | None = None
    query: str = Field(
        default="Explain the current project risk and recommend the most important intervention."
    )


class Intervention(BaseModel):
    action: str
    rationale: str
    priority: str


class IntelligenceResponse(BaseModel):
    project_id: str
    observation_id: str
    summary: str
    risk_explanation: str
    key_evidence: list[str]
    intervention: Intervention
    limitations: list[str]