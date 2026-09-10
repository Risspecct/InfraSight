from pydantic import BaseModel


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
