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

Drop the real model file at the path set by `MODEL_PATH` in `.env`
(defaults to `app/models/model.pkl`). Until it's there, the API runs
on a mock prediction so the rest of the team isn't blocked.

## Run locally

```bash
uvicorn app.main:app --reload
```

- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## How the ML model is integrated

1. `app/models/ml_service.py` loads the model once (cached) via `joblib.load`.
2. `POST /predict` (in `app/api/routes.py`) validates the request body
   against `PredictionRequest` (in `app/schemas/prediction.py`).
3. Validated input is passed to `predict()` in `ml_service.py`, which
   builds the feature vector, calls `model.predict(...)`, and maps the
   raw output to `k_eff`, `reactor_status`, and `uncertainty`.
4. The result is returned as `PredictionResponse`, serialized to JSON.

**TODO once the real model arrives:** confirm the exact feature order/
shape it expects, and how it encodes status/uncertainty in its raw
output — both are marked with `# TODO` in `ml_service.py`.

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
