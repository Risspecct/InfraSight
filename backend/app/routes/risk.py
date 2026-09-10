from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.database import SessionLocal
from app.services.portfolio_risk import get_portfolio_risk


router = APIRouter(
    prefix="/risk",
    tags=["risk"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/portfolio")
def portfolio_risk(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_portfolio_risk(
        db,
        page,
        page_size,
    )
