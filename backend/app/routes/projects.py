from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from db.database import SessionLocal
from db.models import Project

from app.schemas.projects import (
    ProjectDetail,
    ProjectListResponse,
    ProjectSummary,
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
