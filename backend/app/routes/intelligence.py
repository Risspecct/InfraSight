from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import SessionLocal

from app.intelligence.schemas import (
    IntelligenceRequest,
    IntelligenceResponse,
)

from app.intelligence.service import (
    IntelligenceService,
)


router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/projects/{project_id}/observations/{observation_id}",
    response_model=IntelligenceResponse,
)
def project_intelligence(
    project_id: str,
    observation_id: str,
    request: IntelligenceRequest,
    db: Session = Depends(get_db),
):

    try:
        service = IntelligenceService()

        return service.analyze(
            db=db,
            project_id=project_id,
            observation_id=observation_id,
            query=request.query,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
