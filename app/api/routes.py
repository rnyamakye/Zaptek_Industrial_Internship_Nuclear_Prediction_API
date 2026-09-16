from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.models.ml_service import predict as run_prediction
from app.schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictionResponse, status_code=200)
def predict_reactor_behavior(payload: PredictionRequest):
    """
    Accepts enrichment_percent, fuel_density, moderator_density.
    Returns predicted k_eff, reactor_status, and uncertainty (if available).
    """
    try:
        result = run_prediction(payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Catch-all so a model error returns a clean 500 instead of crashing
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    return result
