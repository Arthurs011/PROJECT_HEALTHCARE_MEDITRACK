"""Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


# --------------------------------------------------------------------------- #
#  Vitals
# --------------------------------------------------------------------------- #
class VitalsCreate(BaseModel):
    systolic: int = Field(60, ge=40, le=300)
    diastolic: int = Field(40, ge=20, le=200)
    heart_rate: int = Field(72, ge=20, le=250)
    temperature_c: float = Field(36.6, ge=30, le=45)


class VitalsOut(VitalsCreate):
    model_config = ConfigDict(from_attributes=True)

    recorded_at: datetime


# --------------------------------------------------------------------------- #
#  Visits
# --------------------------------------------------------------------------- #
class VisitCreate(BaseModel):
    visit_date: date | None = None
    reason: str = "General consultation"
    notes: str = ""


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    visit_date: date
    reason: str
    notes: str


# --------------------------------------------------------------------------- #
#  Patients
# --------------------------------------------------------------------------- #
class PatientBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    dob: date
    gender: str = Field(pattern="^[MF]$")
    blood_group: str
    allergies: list[str] = []
    height_cm: float = Field(0, ge=0, le=250)
    weight_kg: float = Field(0, ge=0, le=400)

    @field_validator("blood_group")
    @classmethod
    def valid_blood_group(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in BLOOD_GROUPS:
            raise ValueError("invalid blood group")
        return v


class PatientCreate(PatientBase):
    pass


class PatientOut(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: str
    created_at: datetime

    visits: list[VisitOut] = []
    vitals_history: list[VitalsOut] = []


class PatientSummary(BaseModel):
    id: int
    patient_id: str
    name: str
    age: int
    gender: str
    blood_group: str
    risk_score: float
    risk_label: str


# --------------------------------------------------------------------------- #
#  Risk output
# --------------------------------------------------------------------------- #
class RiskOut(BaseModel):
    patient_id: str
    name: str
    bmi: float
    bmi_category: str
    bp_category: str
    has_fever: bool
    risk_score: float
    risk_label: str
    ml_probability: float | None = None
    ml_label: str | None = None


# --------------------------------------------------------------------------- #
#  Auth
# --------------------------------------------------------------------------- #
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    role: str = "doctor"
    full_name: str = ""

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("admin", "doctor"):
            raise ValueError("role must be 'admin' or 'doctor'")
        return v


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    full_name: str


# --------------------------------------------------------------------------- #
#  Misc
# --------------------------------------------------------------------------- #
class VisitLogLine(BaseModel):
    line: str


class ReportOut(BaseModel):
    total_patients: int
    high_risk_count: int
    moderate_risk_count: int
    low_risk_count: int
    average_age: float
    all_allergies: list[str]
    departments: list[str]
    total_departments: int