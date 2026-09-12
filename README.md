# 🏥 MediTrack v2 — Patient Health Record & Risk Management System

A full-stack **major-project** upgrade of the console MediTrack app: a web-based
patient management system with a **rule-based clinical risk engine**, a
**machine-learning risk-prediction model**, JWT **role-based authentication**,
a REST **API** and a browser **dashboard**.

```
                    FastAPI + SQLite + scikit-learn
```

---

## ✨ What it does

- 🧑‍⚕️ Patient CRUD (name, DOB, gender, blood group, allergies, height/weight)
- 📈 **Longitudinal vitals** — unlimited readings per patient, risk score over time
- 📋 **Visit logging** with date, reason and notes
- ⚕️ **Rule-based risk engine** — BMI category, BP stage, fever, 0–100 risk score
  (reused from the v1 console project, `meditrack/vitals.py`)
- 🤖 **ML prediction** — Random Forest / Logistic Regression predict the
  probability of high-risk from raw vitals (ROC-AUC ≈ 0.91)
- 🔐 **Auth & roles** — JWT tokens; `admin` vs `doctor` permissions (401/403 enforced)
- 📊 **Reports** — risk distribution, average age, allergy inventory,
  recursive hospital-department hierarchy
- 🖥️ **Dashboard** — overview, live patient search, risk cards, vitals/visits
  history, ML metrics page

---

## 🚀 Quick start

```bash
uv sync                 # install dependencies into .venv
uv run python -m ml.train   # train & save the risk model
uv run pytest           # run the test suite (16 tests)
uv run python -m scripts.seed_demo   # optional: load 6 demo patients
uv run uvicorn backend.main:app --reload
```

Open **http://127.0.0.1:8000** and log in:

| Role  | Username      | Password   |
|-------|---------------|------------|
| Admin | `admin`       | `admin123` |
| Doctor| `dr.sharma`   | `doctor123`|

> Requires Python ≥ 3.11 and [uv](https://docs.astral.sh/uv/). Nothing else.

---

## 🗂 Project structure

```
MediTrack/
├── main.py                  # v1 console app (kept as learning baseline)
├── meditrack/               # v1 package — rules reused by the v2 risk engine
├── backend/
│   ├── main.py              # FastAPI app: all routes
│   ├── models.py            # SQLAlchemy ORM: User, Patient, VitalsHistory, Visit
│   ├── schemas.py           # Pydantic request/response models
│   ├── security.py          # bcrypt + JWT + role dependencies
│   ├── risk.py              # rule engine + ML feature extraction
│   ├── db.py                # engine, session, init
│   └── config.py            # settings (.env overridable)
├── ml/
│   ├── generate_data.py     # synthetic clinical dataset (rule-labelled)
│   ├── train.py             # train, evaluate, save artifacts
│   ├── predict.py           # prediction wrapper used by the API
│   └── artifacts/           # risk_model.pkl + metrics.json (gitignored)
├── frontend/                # static dashboard (served at /)
├── scripts/
│   └── seed_demo.py         # load demo patients via the API
├── tests/                   # pytest: risk engine + API
├── docs/
│   ├── SRS.md               # software requirements specification
│   ├── architecture.md      # layered architecture + runbook
│   └── ER.md                # entity–relationship model
├── data/                    # SQLite database lives here
├── requirements.txt
└── pyproject.toml
```

---

## 📚 Documentation

- **Docs:** [SRS](docs/SRS.md) · [Architecture](docs/architecture.md) · [ER model](docs/ER.md)
- **API docs (Swagger):** http://127.0.0.1:8000/docs while the server is running

---

## 🧪 ML pipeline summary

| Step | Tool |
|---|---|
| Data | synthetic generator, 3000 patients, 8 features |
| Label | rule score ≥ 60 → high risk (+2% noise) |
| Models | Logistic Regression vs Random Forest (stratified 75/25) |
| Selection | best ROC-AUC on holdout |
| Evaluation | accuracy, precision, recall, F1, ROC-AUC, permutation importance |

| Model | Accuracy | ROC-AUC | F1 (high-risk) |
|---|---|---|---|
| Logistic Regression | 0.936 | 0.891 | 0.500 |
| Random Forest | 0.976 | 0.913 | 0.845 |

---

## 🔭 Ideas to extend further

- Migrate to PostgreSQL + Alembic migrations; containerise with Docker.
- Train on a real (anonymised) clinical dataset; add cross-validation + SHAP.
- Add a `patient` role so patients can view only their own records.
- Medication allergy-interaction checker; appointment scheduling algorithm.
- Time-series model (LSTM / gradient boosting with lag features) on vital trends.