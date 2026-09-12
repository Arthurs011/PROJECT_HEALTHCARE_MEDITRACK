# Architecture — MediTrack v2

## Layered architecture

```
┌────────────────────────────────────────────────────────────────┐
│  FRONTEND  (static JS dashboard, served by FastAPI)            │
│  index.html · app.js · style.css                                │
└───────────────────────────┬────────────────────────────────────┘
                            │  fetch() + JWT Bearer
┌───────────────────────────▼────────────────────────────────────┐
│  API LAYER  backend/main.py  (FastAPI)                         │
│  routes · Pydantic validation · auth dependencies              │
└───────┬──────────────┬──────────────────┬──────────────────────┘
        │              │                  │
   ┌────▼─────┐   ┌────▼─────┐      ┌────▼───────────────────┐
   │ SERVICE  │   │  AUTH    │      │  ML SERVICE            │
   │ risk.py  │   │ security │      │  ml/predict.py         │
   │ (rules)  │   │ (JWT)    │      │  loads risk_model.pkl  │
   └────┬─────┘   └──────────┘      └────┬───────────────────┘
        │                               │
   ┌────▼──────────────────────────────▼────┐
   │  DATA LAYER  backend/models.py + db.py │
   │  SQLAlchemy ORM ──► SQLite             │
   └─────────────────────────────────────────┘
```

## Components

### Frontend
Static HTML/CSS/vanilla-JS dashboard mounted with Starlette `StaticFiles`.
It calls the REST API and renders risk badges, stat cards, a risk-distribution
bar, patient tables, a vitals/visits timeline and an ML metrics page.

### API layer (`backend/main.py`)
Route definitions, request/response models (Pydantic), and security
dependencies. Every endpoint except `/auth/login` requires a valid JWT;
admin-only endpoints additionally require `role == "admin"`.

### Clinical service (`backend/risk.py`)
Reuses the **v1 console rules** (`meditrack/vitals.py`) as the explainable
baseline: BMI category, BP stage, fever detection and the 0–100 risk score.
It also exposes the feature-extraction used by the ML model, so the rule engine
and the model are benchmarked on the same inputs.

### ML service (`ml/predict.py`)
Loads the serialised sklearn pipeline (`risk_model.pkl`) once, and returns the
probability that a patient is high-risk. If no artifact exists, the API returns
`null` for the ML fields instead of crashing.

### Data layer (`backend/models.py`, `backend/db.py`)
Four ORM entities: `User`, `Patient`, `VitalsHistory`, `Visit`.
SQLite via SQLAlchemy 2.x `Mapped`/`mapped_column` style. `init_db()`
auto-creates tables; `seed_default_admin()` creates default accounts.

## Data flow — risk assessment
1. `GET /patients/{id}/risk`
2. `risk.compute_risk(patient)` → rule score + labels (rule engine)
3. `risk.risk_features(patient)` → feature vector
4. `ml.predict.predict(features)` → probability (if model available)
5. FastAPI serialises to `RiskOut`

## Security model
- Passwords: bcrypt hash.
- Tokens: HMAC-SHA256 JWT, expiry 24h, secret from `backend/config.py`/`.env`.
- Role enforcement via `require_admin` dependency → 403 for doctors.

## Runbook
```bash
uv sync                      # install deps
uv run python -m ml.train    # train + save model artifacts
uv run pytest                # run the test suite
uv run uvicorn backend.main:app --reload    # dev server → http://127.0.0.1:8000
```
Login: `admin / admin123` (admin) or `dr.sharma / doctor123` (doctor).