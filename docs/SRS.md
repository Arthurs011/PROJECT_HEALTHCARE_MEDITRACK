# Software Requirements Specification — MediTrack v2

**Project:** MediTrack — Patient Health Record & Risk Management System
**Version:** 2.0.0
**Status:** Draft for final-year major project

---

## 1. Introduction

### 1.1 Purpose
A small clinic needs a lightweight, secure, web-based system to manage patient
records, automatically compute clinical health-risk scores, triage high-risk
patients, and predict risk using a machine-learning model trained on historical
patient data.

### 1.2 Scope
- CRUD for patient demographics, baseline metrics and allergies.
- Longitudinal vitals recording (time-series of readings per patient).
- Visit logging with date, reason and notes.
- Rule-based clinical risk scoring (BMI, blood pressure, heart rate, fever).
- ML-based high-risk prediction with calibrated probability.
- Role-based access control (admin / doctor) with JWT authentication.
- Reports: risk distribution, department hierarchy, allergy inventory.
- Responsive web dashboard for clinic staff.

### 1.3 Definitions / Abbreviations
| Term | Meaning |
|---|---|
| BMI | Body Mass Index = weight(kg) / height(m)² |
| BP | Blood pressure (systolic/diastolic in mmHg) |
| ROC-AUC | Area under the Receiver Operating Characteristic curve |
| JWT | JSON Web Token |

---

## 2. Overall Description

### 2.1 Users
- **Admin** — creates user accounts, maintains the hospital department hierarchy,
  can delete patient records.
- **Doctor** — records patients, vitals and visits, views risk assessments and ML
  predictions.

### 2.2 Operating Environment
- Python ≥ 3.11, FastAPI, SQLAlchemy, scikit-learn.
- SQLite (dev) / PostgreSQL (future deployment).
- Browser-based dashboard served by the same process.

### 2.3 Assumptions & Dependencies
- No external medical API; all rules are locally implemented.
- Training data is synthetic and risk-labelled by the rule engine; this is clearly
  documented as a modelling simplification.

---

## 3. Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | System SHALL authenticate users with username/password and issue a JWT. |
| FR-02 | System SHALL enforce admin vs doctor permissions on protected endpoints. |
| FR-03 | System SHALL create, read, update, search and delete patient records. |
| FR-04 | System SHALL reject invalid blood groups and malformed demographics. |
| FR-05 | System SHALL store an unbounded history of vitals readings per patient. |
| FR-06 | System SHALL compute BMI category, BP stage, fever flag and a 0–100 rule-based risk score per patient. |
| FR-07 | System SHALL expose an ML prediction (probability of high risk) per patient when a trained model artifact exists. |
| FR-08 | System SHALL log visits and append them to each patient's record. |
| FR-09 | System SHALL produce summary statistics (counts by risk, average age, allergy union). |
| FR-10 | System SHALL serve a web dashboard for all the above operations. |

## 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Response time < 300 ms for CRUD on a clinic-scale dataset. |
| NFR-02 | All API input validated by Pydantic; DB queries parameterised (SQLAlchemy). |
| NFR-03 | Passwords stored as bcrypt hashes; tokens signed with HMAC-SHA256. |
| NFR-04 | Test suite with coverage of the risk engine and the full API surface. |
| NFR-05 | The project MUST be runnable with a single command and no external service. |

---

## 5. External Interface Requirements

### 5.1 REST API (selected endpoints)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | — | issue JWT |
| POST | `/auth/register` | admin | create user |
| GET | `/auth/me` | any | current user |
| POST | `/patients` | any | create patient |
| GET | `/patients?query=` | any | list/search patients with risk summary |
| PATCH | `/patients/{id}` | any | update patient |
| DELETE | `/patients/{id}` | admin | delete patient |
| GET | `/patients/{id}/risk` | any | rule + ML risk assessment |
| GET | `/patients/{id}/risk/trend` | any | risk score over time |
| POST | `/patients/{id}/vitals` | any | add reading |
| POST | `/patients/{id}/visits` | any | log visit |
| GET | `/reports/summary` | any | risk statistics |
| GET | `/reports/departments` | admin | department hierarchy (recursion) |
| GET | `/ml/status` | any | model + metrics info |

### 5.2 Web UI
Login screen, overview dashboard, patient list with live search, patient detail
with risk card / vitals history / visits, add-patient form, ML model page,
department tree.

---

## 6. ML Pipeline Specification

- **Data:** synthetic generator (`ml/generate_data.py`) — 3000 patients, features:
  age, BMI, systolic, diastolic, heart-rate, temperature, allergy count, visit count.
- **Label:** `1 if rule_score >= 60 else 0`, with 2% label noise.
- **Models:** Logistic Regression vs Random Forest (holdout 25%, stratified).
- **Selection:** best by ROC-AUC.
- **Artifacts:** `ml/artifacts/risk_model.pkl` + `metrics.json`.
- **Monitoring:** feature importance via permutation importance.

Current baseline (from a standard training run):
| Metric | Logistic Regression | Random Forest |
|---|---|---|
| Accuracy | 0.936 | 0.976 |
| ROC-AUC | 0.891 | 0.913 |
| F1 (high-risk) | 0.500 | 0.845 |

---

## 7. Acceptance Criteria
1. Fresh clone → `uv sync` → `uv run python -m ml.train` → `uv run pytest` all pass.
2. `uv run uvicorn backend.main:app` serves the dashboard and API.
3. Unauthenticated requests to protected endpoints return 401.
4. A doctor can create a patient, add vitals and see a HIGH/ML prediction.
5. Non-admin users cannot access admin endpoints (403).