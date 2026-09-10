from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import SessionLocal
from app.services.risk_trajectory import get_risk_trajectory


router = APIRouter(
    prefix="/projects",
    tags=["trajectory"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{project_id}/risk-trajectory")
def risk_trajectory(
    project_id: str,
    db: Session = Depends(get_db),
):
    try:
        return get_risk_trajectory(
            db,
            project_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
