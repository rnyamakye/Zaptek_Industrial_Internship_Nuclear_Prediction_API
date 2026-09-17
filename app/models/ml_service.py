"""
Wraps the provided ML model. Swap the TODOs below once the real
model file (.pkl / .joblib / etc.) is in hand.
"""

from functools import lru_cache

from app.core.config import settings
from app.schemas.prediction import PredictionRequest, PredictionResponse


class ModelNotLoadedError(Exception):
    pass


@lru_cache
def _load_model():
    """Load the model once and cache it for the app's lifetime."""
    try:
        import joblib  # TODO: swap for the correct loader (joblib/pickle/onnxruntime/etc.)

        return joblib.load(settings.MODEL_PATH)
    except FileNotFoundError:
        # Lets the rest of the API be built/tested before the real
        # model file is dropped into app/models/.
        return None


def predict(payload: PredictionRequest) -> PredictionResponse:
    model = _load_model()

    if model is None:
        # --- MOCK PATH: remove once the real model is wired in ---
        k_eff = 0.98 + (payload.enrichment_percent * 0.001)
        return PredictionResponse(
            k_eff=round(k_eff, 4),
            reactor_status=classify_status(k_eff),
            uncertainty=None,
        )

    # --- REAL PATH ---
    # TODO: confirm the exact input order/shape the model expects.
    features = [[
        payload.enrichment_percent,
        payload.fuel_density,
        payload.moderator_density,
    ]]
    raw_output = model.predict(features)
    k_eff = float(raw_output[0])

    return PredictionResponse(
        k_eff=round(k_eff, 4),
        reactor_status=classify_status(k_eff),
        uncertainty=None,
    )


def classify_status(k_eff: float) -> str:
    """Matches the ML team's rule from their notebook (not a trained classifier)."""
    if k_eff < 0.95:
        return "Subcritical"
    elif k_eff <= 1.05:
        return "Critical"
    return "Supercritical"
