from sqlalchemy import func
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import PredictionRecord, User
from app.schemas.analytics import AnalyticsSummary, StatusBreakdown, TrendPoint

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _base_query(db: Session, current_user: User, user_id: int | None):
    """
    Same access rule as /predictions: regular users only ever see
    their own data. Admins see everyone's by default, and can narrow
    to one user via ?user_id=.
    """
    query = db.query(PredictionRecord)

    if current_user.role == "admin":
        if user_id is not None:
            query = query.filter(PredictionRecord.user_id == user_id)
    else:
        query = query.filter(PredictionRecord.user_id == current_user.id)

    return query


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: int | None = Query(
        None, description="Admin only: restrict the summary to one user's predictions"
    ),
):
    """
    Overall stats: total predictions, breakdown by reactor status,
    and averages across k_eff, uncertainty, and enrichment_percent.
    """
    query = _base_query(db, current_user, user_id)

    total = query.count()

    status_rows = (
        query.with_entities(
            PredictionRecord.reactor_status, func.count(PredictionRecord.id)
        )
        .group_by(PredictionRecord.reactor_status)
        .all()
    )
    status_breakdown = [
        StatusBreakdown(reactor_status=status or "Unknown", count=count)
        for status, count in status_rows
    ]

    aggregates = query.with_entities(
        func.avg(PredictionRecord.k_eff),
        func.avg(PredictionRecord.uncertainty),
        func.avg(PredictionRecord.enrichment_percent),
        func.min(PredictionRecord.created_at),
        func.max(PredictionRecord.created_at),
    ).first()

    avg_k_eff, avg_uncertainty, avg_enrichment, earliest, latest = aggregates

    return AnalyticsSummary(
        total_predictions=total,
        status_breakdown=status_breakdown,
        avg_k_eff=round(avg_k_eff, 4) if avg_k_eff is not None else None,
        avg_uncertainty=round(avg_uncertainty, 4) if avg_uncertainty is not None else None,
        avg_enrichment_percent=round(avg_enrichment, 4) if avg_enrichment is not None else None,
        earliest_prediction=earliest,
        latest_prediction=latest,
    )


@router.get("/trends", response_model=list[TrendPoint])
def get_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: int | None = Query(
        None, description="Admin only: restrict trends to one user's predictions"
    ),
):
    """
    Predictions per day, with the average k_eff for that day.
    Useful for plotting activity/reactivity over time.
    """
    query = _base_query(db, current_user, user_id)

    day = func.date(PredictionRecord.created_at)

    rows = (
        query.with_entities(day, func.count(PredictionRecord.id), func.avg(PredictionRecord.k_eff))
        .group_by(day)
        .order_by(day)
        .all()
    )

    return [
        TrendPoint(date=str(d), count=count, avg_k_eff=round(avg_k, 4) if avg_k is not None else None)
        for d, count, avg_k in rows
    ]
