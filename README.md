# Nuclear Reactor Behavior Prediction API

A FastAPI backend that wraps a trained machine learning model, letting any
client ask "given these reactor design inputs, what will happen?" over a
simple HTTP request instead of running a Python notebook by hand.

**Project context:** Week 1 deliverable for Backend Development (ML & Backend
Integration) — Zaptek Industrial Internship.

---

## What problem this solves

The ML team trained a model that predicts nuclear reactor behavior from three
design inputs, achieving 99.77% accuracy (R²) on held-out data. A trained
model in a notebook is a research result, not a product — it only runs on
one machine, for one person, at a time. This project turns that model into a
real, always-on API: something a mobile app, a dashboard, or another service
can call directly.

## What it actually predicts

Given three reactor design parameters, the API returns:

| Field | Meaning |
|---|---|
| `k_eff` | The neutron multiplication factor — the core reactivity number. `k_eff = 1.0` means the reactor is in a stable, self-sustaining state. |
| `reactor_status` | A plain-language label: **Subcritical** (`k_eff < 0.95`, reaction dying out), **Critical** (`0.95–1.05`, stable), or **Supercritical** (`k_eff > 1.05`, power increasing) |
| `uncertainty` | How confident the model is in this specific prediction (lower = more confident) |

**Inputs it needs:**

| Field | Meaning | Valid range |
|---|---|---|
| `enrichment_percent` | % of U-235 in the fuel | 2.0 – 5.0 |
| `fuel_density` | how tightly packed the fuel is (g/cm³) | 9.80 – 10.60 |
| `moderator_density` | amount of neutron-slowing material (g/cm³) | 0.95 – 1.05 |

These bounds come directly from the data the model was trained on — values
outside this range are rejected before they ever reach the model.

## How a request flows through the system

```
Client
  ↓  POST /predict  { enrichment_percent, fuel_density, moderator_density }
  ↓
Input validation (Pydantic)     — rejects bad input with a 422, before the model ever runs
  ↓
ML model service                — loads the trained model once, keeps it in memory
  ↓
Model inference                 — Random Forest predicts k_eff; status derived from k_eff;
  ↓                                uncertainty computed from spread across the forest's trees
JSON response                   — { k_eff, reactor_status, uncertainty }
```

## The model itself

`app/models/model.pkl` is not a single model — it's a bundle containing:
- A trained **Random Forest Regressor** that predicts `k_eff` (R² = 0.9977, RMSE = 0.0023)
- The exact **feature order** the model expects
- The **status thresholds** used to turn a `k_eff` number into Subcritical/Critical/Supercritical
- The **valid input ranges** from the training data (mirrored in the API's validation rules)

`uncertainty` isn't guessed — it's the real standard deviation across the
Random Forest's 100 individual trees for that specific input. Trees that
mostly agree with each other → low uncertainty. Trees that disagree → high
uncertainty, meaning that particular input sits in a less certain part of the
model's learned space.

## Project structure

```
app/
├── main.py               # FastAPI app entrypoint + /health check
├── api/routes.py         # the /predict endpoint — HTTP layer only
├── models/
│   ├── ml_service.py     # loads the model bundle, runs inference
│   └── model.pkl         # the trained model bundle itself
├── schemas/
│   └── prediction.py     # Pydantic request/response contracts + validation rules
└── core/
    └── config.py         # environment-based settings
tests/
└── test_predict.py       # automated tests: valid input, invalid input, health check
postman/                  # Postman collection — one request per reactor status,
                           # plus a validation-error example
```

Each piece only does one job: `routes.py` never touches the model directly,
`ml_service.py` never touches HTTP concerns, and `prediction.py` is the single
source of truth both sides agree on. That means any one person can change
their piece without breaking anyone else's.

## Running it locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

- Interactive docs (try it in the browser): **http://localhost:8000/docs**
- Health check: **http://localhost:8000/health**

Example request to `/predict`:

```json
{
  "enrichment_percent": 3.8,
  "fuel_density": 10.3,
  "moderator_density": 1.0
}
```

```json
{
  "k_eff": 1.0054,
  "reactor_status": "Critical",
  "uncertainty": 0.0094
}
```

## Testing

- **Automated**: `pytest` — covers a valid prediction, an invalid (out-of-range)
  input, and the health check.
- **Manual**: the Postman collection in `/postman` — one request per reactor
  status (Subcritical / Critical / Supercritical) plus a validation-error
  example, so you can see both success and failure responses without writing
  any code.

## Deployment

Live on Render, redeploying automatically on every push to `main`. Build and
start commands, plus required environment variables, are set in the Render
dashboard — see `.env.example` for what's needed.

## Team

| Person | Focus |
|---|---|
| Rick (Richard Nyamekye) | Lead — architecture, review, model integration, edge-case tests |
| Reginald Ankomah | Input validation ranges |
| Banasco | Manual verification against notebook results |
| Sakeenah | API documentation |
| Angela | Postman collection |
