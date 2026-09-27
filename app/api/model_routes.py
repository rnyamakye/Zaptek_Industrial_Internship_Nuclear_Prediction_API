from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models import User
from app.models.ml_service import get_model_info
from app.schemas.model_info import ModelInfo

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/info", response_model=ModelInfo)
def model_info(current_user: User = Depends(get_current_user)):
    """
    Metadata about the trained model currently loaded by the API:
    which algorithm it is, what features it expects, the thresholds
    it uses to classify reactor status, the valid input ranges it was
    trained on, and its validation metrics.
    """
    return get_model_info()
