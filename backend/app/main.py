from fastapi import FastAPI
from sqlalchemy import text

from db.database import engine
from app.routes.decision import router as decision_router
from app.routes.projects import router as projects_router
from app.routes.risk import router as risk_router
from app.routes.trajectory import router as trajectory_router
from app.routes.intelligence import router as intelligence_router


app = FastAPI(
    title="InfraSight API",
    version="0.5.0",
)

app.include_router(
    decision_router,
    prefix="/api",
)

app.include_router(
    projects_router,
    prefix="/api",
)

app.include_router(
    risk_router,
    prefix="/api"
)

app.include_router(
    trajectory_router,
    prefix="/api",
)

app.include_router(
    intelligence_router,
    prefix="/api",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "ok"}
