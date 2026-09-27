"""
Wraps the provided ML model bundle (app/models/model.pkl).

The bundle is a dict containing:
  - regressor: trained RandomForestRegressor -> predicts k_eff
  - classifier: trained DecisionTreeClassifier (unused - we use the
    bundled status_thresholds instead, which are exact/deterministic)
  - feature_names: input order the regressor expects
  - status_thresholds: {subcritical_max, supercritical_min}
  - training_data_range: valid input bounds (mirrored in the Pydantic schema)
"""

import numpy as np
import pandas as pd
from functools import lru_cache

from app.core.config import settings
from app.schemas.prediction import PredictionRequest, PredictionResponse


@lru_cache
def _load_model():
    """Load the model bundle once and cache it for the app's lifetime."""
    try:
        import joblib

        return joblib.load(settings.MODEL_PATH)
    except FileNotFoundError:
        # Lets the rest of the API be built/tested before the real
        # model file is dropped into app/models/model.pkl.
        return None


def predict(payload: PredictionRequest) -> PredictionResponse:
    bundle = _load_model()

    if bundle is None:
        # --- MOCK PATH: used only if model.pkl is missing ---
        k_eff = 0.98 + (payload.enrichment_percent * 0.001)
        return PredictionResponse(
            k_eff=round(k_eff, 4),
            reactor_status=classify_status(k_eff, {"subcritical_max": 0.95, "supercritical_min": 1.05}),
            uncertainty=None,
        )

    # --- REAL PATH ---
    regressor = bundle["regressor"]
    feature_names = bundle["feature_names"]
    thresholds = bundle["status_thresholds"]

    feature_map = {
        "enrichment_percent": payload.enrichment_percent,
        "fuel_density": payload.fuel_density,
        "moderator_density": payload.moderator_density,
    }
    features = pd.DataFrame([[feature_map[name] for name in feature_names]], columns=feature_names)

    k_eff = float(regressor.predict(features)[0])

    # Uncertainty: spread of predictions across the forest's individual trees.
    # Individual trees weren't fitted with feature names, so use raw values here.
    tree_preds = np.array([tree.predict(features.values)[0] for tree in regressor.estimators_])
    uncertainty = float(tree_preds.std())

    return PredictionResponse(
        k_eff=round(k_eff, 4),
        reactor_status=classify_status(k_eff, thresholds),
        uncertainty=round(uncertainty, 4),
    )


def classify_status(k_eff: float, thresholds: dict) -> str:
    if k_eff < thresholds["subcritical_max"]:
        return "Subcritical"
    elif k_eff <= thresholds["supercritical_min"]:
        return "Critical"
    return "Supercritical"


def get_model_info() -> dict:
    """
    Metadata about the loaded model, for GET /model/info.
    Falls back to a minimal payload if the real model file isn't present.
    """
    bundle = _load_model()

    if bundle is None:
        return {
            "model_loaded": False,
            "regressor_name": None,
            "feature_names": ["enrichment_percent", "fuel_density", "moderator_density"],
            "status_thresholds": {"subcritical_max": 0.95, "supercritical_min": 1.05},
            "training_data_range": None,
            "metrics": None,
            "sklearn_version": None,
            "trained_at_utc": None,
        }

    return {
        "model_loaded": True,
        "regressor_name": bundle.get("regressor_name"),
        "feature_names": bundle.get("feature_names"),
        "status_thresholds": bundle.get("status_thresholds"),
        "training_data_range": bundle.get("training_data_range"),
        "metrics": bundle.get("metrics"),
        "sklearn_version": bundle.get("sklearn_version"),
        "trained_at_utc": bundle.get("trained_at_utc"),
    }
