# Nuclear Reactor Prediction & Analytics API

A FastAPI backend that wraps a trained machine learning model behind a full,
authenticated, database-backed API — letting any client register, log in,
request reactor behavior predictions, browse their prediction history, and
pull analytics, all over HTTP.

**Project context:** Week 2 deliverable for Backend Development (ML & Backend
Integration) — Zaptek Industrial Internship. Builds directly on the Week 1
prediction API by adding authentication, persistence, and analytics.

---

## What problem this solves

Week 1 turned a trained ML model into a working `/predict` endpoint. Week 2
turns that into an actual platform: predictions are now tied to accounts,
saved permanently, searchable, and summarized — the difference between a
demo and something a real product could be built on top of.

## The workflow, end to end

```
Client
  ↓  register / login
Auth (JWT)                    — issues a token, encodes the user's role
  ↓
Client sends POST /predictions with a token
  ↓
Input validation (Pydantic)   — rejects bad input with a 422
  ↓
ML model service              — loads the trained model once, keeps it in memory
  ↓
Model inference                — Random Forest predicts k_eff, status, uncertainty
  ↓
Database (SQLite + SQLAlchemy) — every prediction is saved, tied to the user and
  ↓                               tagged with the model version that produced it
JSON response
  ↓
Later: GET /predictions (search/filter/sort/paginate) or GET /analytics/*
  to review history and trends
```

## Core concepts

**Authentication.** Every account has a `role` — `user` or `admin`. Regular
users only ever see their own predictions. Admins see everyone's by default,
and can narrow to one user with `?user_id=` on the endpoints that support it.
Tokens are JWTs; the role is encoded so authorization checks don't need an
extra database round-trip.

**What the model predicts.** Given `enrichment_percent` (2–5%), `fuel_density`
(9.80–10.60 g/cm³), and `moderator_density` (0.95–1.05 g/cm³), the model
returns `k_eff` (the neutron multiplication factor), `reactor_status`
(Subcritical / Critical / Supercritical), and `uncertainty` (the spread of
predictions across the Random Forest's 100 individual trees — a real
confidence measure, not a placeholder).

**Every prediction is persisted**, tagged with the `model_version` that
produced it, so results stay traceable even as the model improves over time.

## Endpoints

| Method | Path | What it does |
|---|---|---|
| POST | `/auth/register` | Create an account (role defaults to `user`) |
| POST | `/auth/login` | Log in, get a JWT |
| GET | `/auth/me` | Check who a token belongs to |
| POST | `/predictions` | Run one prediction, save it |
| POST | `/predictions/batch` | Run and save multiple predictions in one call |
| GET | `/predictions` | Search/filter/sort/paginate prediction history |
| GET | `/predictions/{id}` | Get one saved prediction |
| DELETE | `/predictions/{id}` | Delete a saved prediction |
| GET | `/analytics/summary` | Total predictions, status breakdown, and averages |
| GET | `/analytics/trends` | Predictions per day, with average k_eff per day |
| GET | `/health` | Liveness check |

`GET /predictions` supports filtering by status, enrichment range, and date
range, plus sorting and pagination — see `/docs` for the exact query
parameters, since these are still being finalized by the team as of this
writing.

> **Not yet implemented:** `GET /model/info` (model name/version/features).
> This is still open.

## Project structure

```
app/
├── main.py                  # FastAPI app entrypoint, router wiring, table creation
├── api/
│   ├── auth_routes.py       # register / login / me
│   ├── routes.py            # prediction endpoints
│   ├── analytics_routes.py  # summary / trends
│   └── deps.py               # shared dependencies: get_db, get_current_user, require_admin
├── core/
│   ├── config.py             # environment-based settings
│   └── security.py           # password hashing, JWT creation/decoding
├── db/
│   ├── database.py           # SQLAlchemy engine/session setup
│   └── models.py             # User and PredictionRecord tables
├── models/
│   └── ml_service.py         # loads the trained model bundle, runs inference
└── schemas/                  # Pydantic request/response contracts
tests/                        # pytest + FastAPI TestClient
postman/                      # Postman collection covering auth, predictions, analytics
```

## The model itself

`app/models/model.pkl` is a bundle containing a trained **Random Forest
Regressor** (R² ≈ 0.998) plus the exact feature order, status thresholds, and
valid input ranges it was trained on. `ml_service.py` loads it once and keeps
it in memory rather than reloading it per request.

## Running it locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

- Interactive docs: **http://localhost:8000/docs**
- Health check: **http://localhost:8000/health**

Typical flow to try it out: register → login (grab the token) → use the
token as a Bearer token on `/predictions` and `/analytics/*`.

## Testing

```bash
pytest
```

Covers health, valid/invalid predictions, and the analytics endpoints. The
Postman collection in `/postman` covers the same ground manually, plus
authentication and validation-error cases.

## Deployment

Live on Render, redeploying automatically on every push to `main`.

## Team

| Person | Focus |
|---|---|
| Rick (Richard Nyamekye) | Lead — architecture, auth, ML integration, search/filter/pagination, analytics |
| Reginald Ankomah | Prediction history filtering/access-control refinements |
| Banasco | Prediction endpoints (single + batch) |
| Sakeenah | Database models, API documentation |
| Angela | Postman collection |
