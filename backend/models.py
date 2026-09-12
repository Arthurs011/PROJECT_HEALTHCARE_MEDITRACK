"""SQLAlchemy ORM models for MediTrack v2.

Tables
------
User           -- login accounts with roles (admin / doctor)
Patient        -- demographic + baseline data
VitalsHistory  -- one row per recorded vitals reading (latest = current)
Visit          -- one row per patient visit
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

ROLES = ("admin", "doctor")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="doctor")
    full_name: Mapped[str] = mapped_column(String(100), default="")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    dob: Mapped[date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(1))
    blood_group: Mapped[str] = mapped_column(String(5))
    allergies: Mapped[list] = mapped_column(Text, default="")  # comma-separated
    # Baseline body metrics
    height_cm: Mapped[float] = mapped_column(Float, default=0.0)
    weight_kg: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    vitals_history: Mapped[list["VitalsHistory"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="VitalsHistory.recorded_at",
    )
    visits: Mapped[list["Visit"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="Visit.date",
    )


class VitalsHistory(Base):
    __tablename__ = "vitals_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    systolic: Mapped[int] = mapped_column(Integer, default=120)
    diastolic: Mapped[int] = mapped_column(Integer, default=80)
    heart_rate: Mapped[int] = mapped_column(Integer, default=72)
    temperature_c: Mapped[float] = mapped_column(Float, default=36.6)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    patient: Mapped["Patient"] = relationship(back_populates="vitals_history")


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, default=date.today)
    reason: Mapped[str] = mapped_column(String(255), default="General consultation")
    notes: Mapped[str] = mapped_column(Text, default="")

    patient: Mapped["Patient"] = relationship(back_populates="visits")