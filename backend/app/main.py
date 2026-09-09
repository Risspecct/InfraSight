from fastapi import FastAPI
from sqlalchemy import text

from db.database import engine
from app.routes.decision import router as decision_router


app = FastAPI(
    title="InfraSight API",
    version="0.1.0",
)


app.include_router(decision_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "ok"}
