from fastapi import FastAPI

from app.api.auth_routes import router as auth_router
from app.api.routes import router as predict_router
from app.core.config import settings
from app.db.database import Base, engine
from app import db_models

# Creates any tables (User, and Predictions once Reginald's model lands)
# that don't exist yet. Safe to call on every startup.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Nuclear Reactor Prediction & Analytics API",
    description="Wraps an ML model that predicts k_eff, reactor status, and uncertainty.",
    version="2.0.0",
)

app.include_router(auth_router)
app.include_router(predict_router)


@app.get("/health", tags=["health"])
def health_check():
    """Simple liveness check. Useful for Render's health checks."""
    return {"status": "ok", "env": settings.ENV}