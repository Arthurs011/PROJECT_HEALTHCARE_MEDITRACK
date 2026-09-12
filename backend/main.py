"""MediTrack v2 — FastAPI application.

Endpoints
---------
auth            /auth/login, /auth/register, /auth/me
patients        CRUD + search + risk
vitals          add / list readings
visits          add / list
ml              model status + per-patient prediction
reports         summary + department hierarchy (v1 recursion)
static          frontend dashboard served at /
"""

import json
import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from meditrack import analytics, data, utils, vitals

from . import models, schemas
from .config import PROJECT_ROOT, settings
from .db import get_db, init_db
from .risk import compute_risk, patient_age, risk_features
from .schemas import RiskOut
from .security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    seed_default_admin,
    verify_password,
)
from ml import predict as ml_predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from .db import SessionLocal

    with SessionLocal() as db:
        seed_default_admin(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Patient Health Record & Risk Management System "
    "(v2: FastAPI + SQLAlchemy + scikit-learn)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #
def _allergies_to_db(items: list[str]) -> str:
    return ",".join(sorted({a.strip().lower() for a in items if a.strip()}))


def _allergies_from_db(raw: str) -> list[str]:
    return [a for a in (raw or "").split(",") if a]


def _patient_out(p: models.Patient) -> schemas.PatientOut:
    return schemas.PatientOut(
        id=p.id,
        patient_id=p.patient_id,
        name=p.name,
        dob=p.dob,
        gender=p.gender,
        blood_group=p.blood_group,
        allergies=_allergies_from_db(p.allergies),
        height_cm=p.height_cm,
        weight_kg=p.weight_kg,
        created_at=p.created_at,
        visits=[
            schemas.VisitOut(
                id=v.id, visit_date=v.date, reason=v.reason, notes=v.notes
            )
            for v in p.visits
        ],
        vitals_history=[
            schemas.VitalsOut.model_validate(v) for v in p.vitals_history
        ],
    )


def _get_patient_or_404(patient_id: str, db: Session) -> models.Patient:
    p = db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()
    if p is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return p


def _risk_out(p: models.Patient) -> RiskOut:
    rule = compute_risk(p)
    proba = label = None
    if ml_predict.available():
        try:
            proba, label = ml_predict.predict(risk_features(p))
        except Exception:
            proba = label = None
    return RiskOut(
        patient_id=p.patient_id,
        name=p.name,
        bmi=rule["bmi"],
        bmi_category=rule["bmi_category"],
        bp_category=rule["bp_category"],
        has_fever=rule["has_fever"],
        risk_score=rule["risk_score"],
        risk_label=rule["risk_label"],
        ml_probability=proba,
        ml_label=label,
    )


# --------------------------------------------------------------------------- #
#  Auth
# --------------------------------------------------------------------------- #
@app.post("/auth/login", response_model=schemas.TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token(user.username, user.role)
    return schemas.TokenOut(
        access_token=token, role=user.role, username=user.username
    )


@app.post("/auth/register", response_model=schemas.UserOut,
          dependencies=[Depends(require_admin)])
def register(body: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == body.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = models.User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
        full_name=body.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user


# --------------------------------------------------------------------------- #
#  Patients
# --------------------------------------------------------------------------- #
@app.post("/patients", response_model=schemas.PatientOut, status_code=201)
def create_patient(
    body: schemas.PatientCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    patient_id = utils.generate_patient_id()
    # ensure uniqueness in case of collision
    while db.query(models.Patient).filter(
        models.Patient.patient_id == patient_id
    ).first():
        patient_id = utils.generate_patient_id()

    p = models.Patient(
        patient_id=patient_id,
        name=utils.clean_name(body.name),
        dob=body.dob,
        gender=body.gender.upper(),
        blood_group=body.blood_group,
        allergies=_allergies_to_db(body.allergies),
        height_cm=body.height_cm,
        weight_kg=body.weight_kg,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _patient_out(p)


@app.get("/patients", response_model=list[schemas.PatientSummary])
def list_patients(
    query: str = Query("", description="filter by name substring"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    q = db.query(models.Patient)
    if query.strip():
        q = q.filter(models.Patient.name.ilike(f"%{query.strip()}%"))
    patients = q.order_by(models.Patient.name).all()
    summaries = []
    for p in patients:
        rule = compute_risk(p)
        summaries.append(
            schemas.PatientSummary(
                id=p.id,
                patient_id=p.patient_id,
                name=p.name,
                age=patient_age(p),
                gender=p.gender,
                blood_group=p.blood_group,
                risk_score=rule["risk_score"],
                risk_label=rule["risk_label"],
            )
        )
    summaries.sort(key=lambda s: (-s.risk_score, s.name))
    return summaries


@app.get("/patients/{patient_id}", response_model=schemas.PatientOut)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    return _patient_out(_get_patient_or_404(patient_id, db))


@app.patch("/patients/{patient_id}", response_model=schemas.PatientOut)
def update_patient(
    patient_id: str,
    body: schemas.PatientBase,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    p = _get_patient_or_404(patient_id, db)
    p.name = utils.clean_name(body.name)
    p.dob = body.dob
    p.gender = body.gender.upper()
    p.blood_group = body.blood_group
    p.allergies = _allergies_to_db(body.allergies)
    p.height_cm = body.height_cm
    p.weight_kg = body.weight_kg
    db.commit()
    db.refresh(p)
    return _patient_out(p)


@app.delete("/patients/{patient_id}", status_code=204)
def delete_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    p = _get_patient_or_404(patient_id, db)
    db.delete(p)
    db.commit()


@app.get("/patients/{patient_id}/risk", response_model=RiskOut)
def patient_risk(
    patient_id: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    p = _get_patient_or_404(patient_id, db)
    return _risk_out(p)


@app.get("/patients/{patient_id}/risk/trend")
def risk_trend(
    patient_id: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Per-reading rule scores so the dashboard can plot risk over time."""
    p = _get_patient_or_404(patient_id, db)
    series = []
    for v in p.vitals_history:
        proxy = {
            "vitals": {
                "height_cm": p.height_cm,
                "weight_kg": p.weight_kg,
                "systolic": v.systolic,
                "diastolic": v.diastolic,
                "heart_rate": v.heart_rate,
                "temperature_c": v.temperature_c,
            }
        }
        series.append(
            {
                "recorded_at": v.recorded_at.isoformat(),
                "risk_score": int(vitals.risk_score(proxy)),
            }
        )
    return {"patient_id": p.patient_id, "series": series}


# --------------------------------------------------------------------------- #
#  Vitals
# --------------------------------------------------------------------------- #
@app.post("/patients/{patient_id}/vitals", response_model=schemas.VitalsOut,
          status_code=201)
def add_vitals(
    patient_id: str,
    body: schemas.VitalsCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    p = _get_patient_or_404(patient_id, db)
    v = models.VitalsHistory(
        patient_id=p.id,
        systolic=body.systolic,
        diastolic=body.diastolic,
        heart_rate=body.heart_rate,
        temperature_c=body.temperature_c,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@app.get("/patients/{patient_id}/vitals", response_model=list[schemas.VitalsOut])
def list_vitals(
    patient_id: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    p = _get_patient_or_404(patient_id, db)
    return p.vitals_history


# --------------------------------------------------------------------------- #
#  Visits
# --------------------------------------------------------------------------- #
@app.post("/patients/{patient_id}/visits", response_model=schemas.VisitOut,
          status_code=201)
def add_visit(
    patient_id: str,
    body: schemas.VisitCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    p = _get_patient_or_404(patient_id, db)
    v = models.Visit(
        patient_id=p.id,
        date=body.visit_date or date.today(),
        reason=body.reason or "General consultation",
        notes=body.notes,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return schemas.VisitOut(
        id=v.id, visit_date=v.date, reason=v.reason, notes=v.notes
    )


@app.get("/patients/{patient_id}/visits", response_model=list[schemas.VisitOut])
def list_visits(
    patient_id: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    p = _get_patient_or_404(patient_id, db)
    return [
        schemas.VisitOut(id=v.id, visit_date=v.date, reason=v.reason, notes=v.notes)
        for v in p.visits
    ]


# --------------------------------------------------------------------------- #
#  ML
# --------------------------------------------------------------------------- #
@app.get("/ml/status")
def ml_status(_: models.User = Depends(get_current_user)):
    if not ml_predict.available():
        return {
            "model_available": False,
            "message": "Run `uv run python -m ml.train` to train and save a model.",
        }
    import json
    import os

    metrics_path = os.path.join(settings.model_artifact_dir, "metrics.json")
    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)
    return {"model_available": True, **metrics}


# --------------------------------------------------------------------------- #
#  Reports
# --------------------------------------------------------------------------- #
@app.get("/reports/departments")
def departments(
    _: models.User = Depends(require_admin),
):
    return {
        "total": analytics.count_departments(data.HOSPITAL),
        "tree": analytics.list_departments(data.HOSPITAL),
    }


@app.get("/reports/summary", response_model=schemas.ReportOut)
def summary(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    patients = db.query(models.Patient).all()
    high = mod = low = 0
    ages, allergies = [], set()
    for p in patients:
        rule = compute_risk(p)
        if rule["risk_label"] == "HIGH":
            high += 1
        elif rule["risk_label"] == "MODERATE":
            mod += 1
        else:
            low += 1
        ages.append(patient_age(p))
        allergies.update(_allergies_from_db(p.allergies))

    return schemas.ReportOut(
        total_patients=len(patients),
        high_risk_count=high,
        moderate_risk_count=mod,
        low_risk_count=low,
        average_age=round(sum(ages) / len(ages), 1) if ages else 0.0,
        all_allergies=sorted(allergies),
        departments=analytics.list_departments(data.HOSPITAL),
        total_departments=analytics.count_departments(data.HOSPITAL),
    )


# --------------------------------------------------------------------------- #
#  Static frontend
# --------------------------------------------------------------------------- #
frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")