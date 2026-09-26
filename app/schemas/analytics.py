from datetime import datetime

from pydantic import BaseModel


class StatusBreakdown(BaseModel):
    reactor_status: str
    count: int


class AnalyticsSummary(BaseModel):
    total_predictions: int
    status_breakdown: list[StatusBreakdown]
    avg_k_eff: float | None
    avg_uncertainty: float | None
    avg_enrichment_percent: float | None
    earliest_prediction: datetime | None
    latest_prediction: datetime | None


class TrendPoint(BaseModel):
    date: str
    count: int
    avg_k_eff: float | None
