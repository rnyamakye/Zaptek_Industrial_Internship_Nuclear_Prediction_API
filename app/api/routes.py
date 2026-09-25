from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import PredictionRecord, User
from app.models.ml_service import predict as run_prediction
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    PredictionRecordResponse,
)

router = APIRouter(
    prefix="/predictions",
    tags=["predictions"],
)


MODEL_VERSION = "v1.0"


@router.post(
    "",
    response_model=PredictionRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_prediction(
    payload: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run a reactor prediction and save the result
    for the currently authenticated user.
    """

    try:
        result = run_prediction(payload)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )

    prediction = PredictionRecord(
        user_id=current_user.id,
        model_version=MODEL_VERSION,

        enrichment_percent=payload.enrichment_percent,
        fuel_density=payload.fuel_density,
        moderator_density=payload.moderator_density,

        k_eff=result.k_eff,
        reactor_status=result.reactor_status,
        uncertainty=result.uncertainty,
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return prediction


@router.post(
    "/batch",
    response_model=list[PredictionRecordResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_batch_predictions(
    payloads: list[PredictionRequest],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run multiple reactor predictions and save all results
    for the currently authenticated user.
    """

    if not payloads:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch cannot be empty",
        )

    predictions = []

    try:
        for payload in payloads:

            result = run_prediction(payload)

            prediction = PredictionRecord(
                user_id=current_user.id,
                model_version=MODEL_VERSION,

                enrichment_percent=payload.enrichment_percent,
                fuel_density=payload.fuel_density,
                moderator_density=payload.moderator_density,

                k_eff=result.k_eff,
                reactor_status=result.reactor_status,
                uncertainty=result.uncertainty,
            )

            db.add(prediction)
            predictions.append(prediction)

        db.commit()

        for prediction in predictions:
            db.refresh(prediction)

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}",
        )

    return predictions


@router.get(
    "",
    response_model=list[PredictionRecordResponse],
)
def get_predictions(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by reactor status, e.g. Critical"
    ),
    enrichment_min: float | None = Query(None, description="Minimum enrichment_percent"),
    enrichment_max: float | None = Query(None, description="Maximum enrichment_percent"),
    date_from: datetime | None = Query(None, description="Only predictions created on/after this timestamp"),
    date_to: datetime | None = Query(None, description="Only predictions created on/before this timestamp"),
    user_id: int | None = Query(
        None, description="Admin only: filter by a specific user's predictions"
    ),
    sort_by: Literal["created_at", "k_eff", "enrichment_percent"] = Query(
        "created_at", description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max number of records to return"),
):
    """
    Get prediction history, with search/filter/sort/pagination.

    Regular users only ever see their own predictions. Admins see
    everyone's by default, and can optionally narrow to one user via
    ?user_id=.
    """

    query = db.query(PredictionRecord)

    if current_user.role == "admin":
        if user_id is not None:
            query = query.filter(PredictionRecord.user_id == user_id)
        # else: no user filter -> admin sees all users' predictions
    else:
        query = query.filter(PredictionRecord.user_id == current_user.id)

    if status_filter is not None:
        query = query.filter(PredictionRecord.reactor_status.ilike(status_filter))

    if enrichment_min is not None:
        query = query.filter(PredictionRecord.enrichment_percent >= enrichment_min)

    if enrichment_max is not None:
        query = query.filter(PredictionRecord.enrichment_percent <= enrichment_max)

    if date_from is not None:
        query = query.filter(PredictionRecord.created_at >= date_from)

    if date_to is not None:
        query = query.filter(PredictionRecord.created_at <= date_to)

    total = query.count()

    sort_column = getattr(PredictionRecord, sort_by)
    sort_column = sort_column.asc() if sort_order == "asc" else sort_column.desc()

    predictions = (
        query.order_by(sort_column)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Lets clients page through results without changing the response shape.
    response.headers["X-Total-Count"] = str(total)

    return predictions


@router.get(
    "/{prediction_id}",
    response_model=PredictionRecordResponse,
)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get one prediction by ID.

    Users can only access their own predictions. Admins can access any.
    """

    query = db.query(PredictionRecord).filter(PredictionRecord.id == prediction_id)

    if current_user.role != "admin":
        query = query.filter(PredictionRecord.user_id == current_user.id)

    prediction = query.first()

    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    return prediction


@router.delete(
    "/{prediction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a prediction.

    Users can only delete their own predictions. Admins can delete any.
    """

    query = db.query(PredictionRecord).filter(PredictionRecord.id == prediction_id)

    if current_user.role != "admin":
        query = query.filter(PredictionRecord.user_id == current_user.id)

    prediction = query.first()

    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    db.delete(prediction)
    db.commit()

    return None


# from fastapi import APIRouter, HTTPException
# from pydantic import ValidationError

# from app.models.ml_service import predict as run_prediction
# from app.schemas.prediction import PredictionRequest, PredictionResponse

# router = APIRouter(tags=["prediction"])


# @router.post("/predict", response_model=PredictionResponse, status_code=200)
# def predict_reactor_behavior(payload: PredictionRequest):
#     """
#     Accepts enrichment_percent, fuel_density, moderator_density.
#     Returns predicted k_eff, reactor_status, and uncertainty (if available).
#     """
#     try:
#         result = run_prediction(payload)
#     except ValidationError as e:
#         raise HTTPException(status_code=422, detail=str(e))
#     except Exception as e:
#         # Catch-all so a model error returns a clean 500 instead of crashing
#         raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

#     return result