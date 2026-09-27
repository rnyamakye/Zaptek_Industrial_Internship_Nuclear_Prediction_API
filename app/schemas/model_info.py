from datetime import datetime

from pydantic import BaseModel


class ModelInfo(BaseModel):
    model_loaded: bool
    regressor_name: str | None = None
    feature_names: list[str] | None = None
    status_thresholds: dict | None = None
    training_data_range: dict | None = None
    metrics: dict | None = None
    sklearn_version: str | None = None
    trained_at_utc: datetime | None = None
