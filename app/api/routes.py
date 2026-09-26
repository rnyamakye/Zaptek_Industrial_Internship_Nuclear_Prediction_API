from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc
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


# ==========================================================
# CREATE SINGLE PREDICTION
# ==========================================================

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


# ==========================================================
# BATCH PREDICTIONS
# ==========================================================

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


# ==========================================================
# PREDICTION HISTORY
# SEARCH / FILTER / SORT / PAGINATION
# ==========================================================

@router.get(
    "",
    response_model=list[PredictionRecordResponse],
    summary="Get prediction history",
    description=(
        "Retrieve prediction history with optional filtering, "
        "sorting, and pagination."
    ),
)
def get_predictions(
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Filter predictions by reactor status.",
    ),
    min_enrichment: float | None = Query(
        None,
        description="Minimum uranium enrichment percentage.",
    ),
    max_enrichment: float | None = Query(
        None,
        description="Maximum uranium enrichment percentage.",
    ),
    user_id: int | None = Query(
        None,
        description="Filter predictions by user ID. Admin users can use this filter.",
    ),
    start_date: datetime | None = Query(
        None,
        description="Return predictions created on or after this date.",
    ),
    end_date: datetime | None = Query(
        None,
        description="Return predictions created on or before this date.",
    ),
    sort_by: Literal[
        "created_at",
        "enrichment",
        "k_eff",
        "status",
    ] = Query(
        "created_at",
        description="Field to sort by.",
    ),
    order: Literal["asc", "desc"] = Query(
        "desc",
        description="Sort order: ascending or descending.",
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number.",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of predictions per page.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get prediction history with filtering, sorting, and pagination.

    Normal users can only view their own predictions.
    Admin users can view predictions from all users and
    optionally filter by user ID.
    """

    # Start the database query
    query = db.query(PredictionRecord)

    # ------------------------------------------------------
    # USER ACCESS CONTROL
    # ------------------------------------------------------

    if current_user.role != "admin":
        # Normal users can only see their own predictions
        query = query.filter(
            PredictionRecord.user_id == current_user.id
        )

    elif user_id is not None:
        # Admin users can filter by a specific user
        query = query.filter(
            PredictionRecord.user_id == user_id
        )

    # ------------------------------------------------------
    # FILTER BY REACTOR STATUS
    # ------------------------------------------------------

    if status_filter:
        query = query.filter(
            PredictionRecord.reactor_status == status_filter
        )

    # ------------------------------------------------------
    # FILTER BY ENRICHMENT RANGE
    # ------------------------------------------------------

    if min_enrichment is not None:
        query = query.filter(
            PredictionRecord.enrichment_percent >= min_enrichment
        )

    if max_enrichment is not None:
        query = query.filter(
            PredictionRecord.enrichment_percent <= max_enrichment
        )

    # ------------------------------------------------------
    # FILTER BY DATE RANGE
    # ------------------------------------------------------

    if start_date is not None:
        query = query.filter(
            PredictionRecord.created_at >= start_date
        )

    if end_date is not None:
        query = query.filter(
            PredictionRecord.created_at <= end_date
        )

    # ------------------------------------------------------
    # SORTING
    # ------------------------------------------------------

    sort_fields = {
        "created_at": PredictionRecord.created_at,
        "enrichment": PredictionRecord.enrichment_percent,
        "k_eff": PredictionRecord.k_eff,
        "status": PredictionRecord.reactor_status,
    }

    sort_column = sort_fields[sort_by]

    if order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # ------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------

    skip = (page - 1) * limit

    predictions = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )

    return predictions


# ==========================================================
# GET ONE PREDICTION
# ==========================================================

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

    Users can only access their own predictions.
    """

    prediction = (
        db.query(PredictionRecord)
        .filter(
            PredictionRecord.id == prediction_id,
            PredictionRecord.user_id == current_user.id,
        )
        .first()
    )

    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    return prediction


# ==========================================================
# DELETE ONE PREDICTION
# ==========================================================

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
    Delete a prediction belonging to the currently
    authenticated user.
    """

    prediction = (
        db.query(PredictionRecord)
        .filter(
            PredictionRecord.id == prediction_id,
            PredictionRecord.user_id == current_user.id,
        )
        .first()
    )

    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    db.delete(prediction)
    db.commit()

    return None
