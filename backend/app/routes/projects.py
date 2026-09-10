from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from db.database import SessionLocal
from db.models import Project, ProjectObservation

from app.services.explanation import explain_project
from app.services.backtest import backtest_project
from app.services.risk_assessment import assess_project

from app.schemas.projects import (
    ObservationListResponse,
    ObservationResponse,
    PredictionResponse,
    ProjectDetail,
    ProjectListResponse,
    ProjectSummary,
    ExplanationResponse,
    BacktestResponse,
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=ProjectListResponse)
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.scalar(
        select(func.count()).select_from(Project)
    )

    total_pages = (total + page_size - 1) // page_size

    projects = db.scalars(
        select(Project)
        .order_by(Project.canonical_project_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = [
        ProjectSummary(
            project_id=project.project_id,
            project_code=project.canonical_project_code,
            project_name=project.canonical_project_name,
            agency=project.canonical_agency,
            state=project.canonical_state,
            sector=project.canonical_sector,
            first_report_date=project.first_report_date,
            last_report_date=project.last_report_date,
            observation_count=project.observation_count,
            identity_confidence=project.identity_confidence,
        )
        for project in projects
    ]

    return ProjectListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return ProjectDetail(
        project_id=project.project_id,
        project_code=project.canonical_project_code,
        project_name=project.canonical_project_name,
        agency=project.canonical_agency,
        state=project.canonical_state,
        sector=project.canonical_sector,
        first_report_date=project.first_report_date,
        last_report_date=project.last_report_date,
        observation_count=project.observation_count,
        identity_confidence=project.identity_confidence,
    )

@router.get(
    "/{project_id}/observations",
    response_model=ObservationListResponse,
)
def get_project_observations(
    project_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    project_exists = db.get(Project, project_id)

    if project_exists is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    total = db.scalar(
        select(func.count())
        .select_from(ProjectObservation)
        .where(ProjectObservation.project_id == project_id)
    )

    total_pages = (total + page_size - 1) // page_size

    observations = db.scalars(
        select(ProjectObservation)
        .where(ProjectObservation.project_id == project_id)
        .order_by(ProjectObservation.report_date)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = [
        ObservationResponse(
            observation_id=o.observation_id,
            project_id=o.project_id,
            project_code=o.project_code,
            serial_no=o.serial_no,
            project_name=o.project_name,
            agency=o.agency,
            state=o.state,
            sector=o.sector,
            report_date=o.report_date,
            approval_date=o.approval_date,
            approval_date_revised=o.approval_date_revised,
            original_cost_crore=o.original_cost_crore,
            revised_cost_crore=o.revised_cost_crore,
            anticipated_cost_crore=o.anticipated_cost_crore,
            cost_overrun_original_crore=o.cost_overrun_original_crore,
            cost_overrun_revised_crore=o.cost_overrun_revised_crore,
            cumulative_expenditure_crore=o.cumulative_expenditure_crore,
            original_completion_date=o.original_completion_date,
            revised_completion_date=o.revised_completion_date,
            anticipated_completion_date=o.anticipated_completion_date,
            time_overrun_original_months=o.time_overrun_original_months,
            time_overrun_revised_months=o.time_overrun_revised_months,
            additional_delay_months=o.additional_delay_months,
            milestones_achieved=o.milestones_achieved,
            milestones_total=o.milestones_total,
            physical_progress_pct=o.physical_progress_pct,
            delay_reason=o.delay_reason,
            status=o.status,
            source_report=o.source_report,
            source_table=o.source_table,
            source_page=o.source_page,
            source_serial_no=o.source_serial_no,
        )
        for o in observations
    ]

    return ObservationListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post(
    "/{project_id}/predict",
    response_model=PredictionResponse,
)
def predict_project_endpoint(
    project_id: str,
    observation_id: str,
    db: Session = Depends(get_db),
):
    try:
        return assess_project(
            db,
            project_id,
            observation_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.get(
    "/{project_id}/explanation",
    response_model=ExplanationResponse,
)
def get_project_explanation(
    project_id: str,
    observation_id: str,
    top_k: int = 5,
    db: Session = Depends(get_db),
):
    observation = (
        db.query(ProjectObservation)
        .filter(
            ProjectObservation.project_id == project_id,
            ProjectObservation.observation_id == observation_id,
        )
        .first()
    )

    if observation is None:
        raise HTTPException(
            status_code=404,
            detail="Observation not found",
        )

    if top_k < 1 or top_k > 10:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 10",
        )

    return explain_project(
        db,
        project_id,
        observation_id,
        top_k,
    )


@router.get(
    "/{project_id}/backtest",
    response_model=BacktestResponse,
)
def get_project_backtest(
    project_id: str,
    observation_id: str,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    try:
        return backtest_project(
            db,
            project_id,
            observation_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
