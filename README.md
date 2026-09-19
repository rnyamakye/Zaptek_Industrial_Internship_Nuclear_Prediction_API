# Nuclear Reactor Behavior Prediction API

FastAPI service wrapping an ML model that predicts k_eff, reactor status,
and uncertainty from three reactor design inputs.

## Project structure

```
app/
├── main.py              # FastAPI app entrypoint
├── api/routes.py        # /predict endpoint
├── models/ml_service.py # loads the model + runs inference
├── schemas/prediction.py# Pydantic request/response models
└── core/config.py       # environment-based settings
tests/
└── test_predict.py      # basic endpoint tests
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

The real trained model is already included at `app/models/model.pkl`
and loaded automatically. If it's ever missing (e.g. `.gitignore`
excludes `*.pkl` by default), the API falls back to a mock prediction
so the rest of the team isn't blocked.

## Run locally

```bash
uvicorn app.main:app --reload
```

- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## How the ML model is integrated

`app/models/model.pkl` is a bundle (a dict), not a bare model:
- `regressor`: trained `RandomForestRegressor` — predicts `k_eff` (R\u00b2 0.9977)
- `classifier`: a `DecisionTreeClassifier` — present but unused, since the
  bundle also ships exact deterministic thresholds (see below)
- `feature_names`: `['enrichment_percent', 'fuel_density', 'moderator_density']`
- `status_thresholds`: `{subcritical_max: 0.95, supercritical_min: 1.05}`
- `training_data_range`: valid input bounds, mirrored in `schemas/prediction.py`

Flow:
1. `app/models/ml_service.py` loads the bundle once (cached) via `joblib.load`.
2. `POST /predict` validates the request against `PredictionRequest`.
3. `predict()` builds a feature DataFrame in the bundle's expected column
   order, runs `regressor.predict(...)` for `k_eff`, classifies status using
   the bundle's own thresholds, and estimates `uncertainty` as the standard
   deviation of predictions across the forest's 100 individual trees.
4. The result is returned as `PredictionResponse`, serialized to JSON.

## Testing

```bash
pytest
```

## Deployment (Render)

1. Push this repo to GitHub.
2. On Render: New Web Service → connect repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add `MODEL_PATH` and `ENV` as environment variables.
