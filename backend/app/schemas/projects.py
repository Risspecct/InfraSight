from pydantic import BaseModel
from app.decision.schemas import RiskComponent


class ProjectSummary(BaseModel):
    project_id: str
    project_code: str | None
    project_name: str
    agency: str | None
    state: str | None
    sector: str | None
    first_report_date: str
    last_report_date: str
    observation_count: int
    identity_confidence: str


class ProjectListResponse(BaseModel):
    items: list[ProjectSummary]
    page: int
    page_size: int
    total: int
    total_pages: int


class ProjectDetail(ProjectSummary):
    pass


class ObservationResponse(BaseModel):
    observation_id: str
    project_id: str
    project_code: str | None
    serial_no: int | None
    project_name: str
    agency: str | None
    state: str | None
    sector: str

    report_date: str
    approval_date: str
    approval_date_revised: str | None

    original_cost_crore: float
    revised_cost_crore: float | None
    anticipated_cost_crore: float | None

    cost_overrun_original_crore: float | None
    cost_overrun_revised_crore: float | None
    cumulative_expenditure_crore: float | None

    original_completion_date: str | None
    revised_completion_date: str | None
    anticipated_completion_date: str | None

    time_overrun_original_months: float | None
    time_overrun_revised_months: float | None
    additional_delay_months: float | None

    milestones_achieved: int
    milestones_total: int

    physical_progress_pct: float | None
    delay_reason: str | None
    status: str | None

    source_report: str
    source_table: str
    source_page: int
    source_serial_no: int


class ObservationListResponse(BaseModel):
    items: list[ObservationResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class PredictionResponse(BaseModel):
    project_id: str
    observation_id: str
    prediction_date: str

    cost_overrun_probability: float
    schedule_overrun_probability: float

    cost_risk: RiskComponent
    schedule_risk: RiskComponent

    risk_level: str
    priority_score: float
    early_warning: bool
