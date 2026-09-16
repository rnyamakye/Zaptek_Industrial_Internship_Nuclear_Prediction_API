from fastapi import FastAPI
from app.api.routes import router as predict_router
from app.core.config import settings

app = FastAPI(
    title="Nuclear Reactor Behavior Prediction API",
    description="Wraps an ML model that predicts k_eff, reactor status, and uncertainty.",
    version="1.0.0",
)

app.include_router(predict_router)


@app.get("/health", tags=["health"])
def health_check():
    """Simple liveness check. Useful for Render's health checks."""
    return {"status": "ok", "env": settings.ENV}
