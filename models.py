import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Time,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    Index,
    text,
)
from sqlalchemy.orm import relationship

from database import Base


class AppointmentStatus(str, enum.Enum):
    booked = "booked"
    cancelled = "cancelled"


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    speciality = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    working_hours_start = Column(Time, nullable=False)
    working_hours_end = Column(Time, nullable=False)
    break_start = Column(Time, nullable=False)
    break_end = Column(Time, nullable=False)

    appointments = relationship("Appointment", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    appointments = relationship("Appointment", back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    status = Column(
        SAEnum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        default=AppointmentStatus.booked,
    )
    cancellation_reason = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

    __table_args__ = (
        # Prevents two BOOKED appointments for the same doctor at the same
        # start_time. This is a partial index — cancelled rows are excluded,
        # so a freed slot becomes rebookable, and rescheduling works by
        # updating start_time on the same row (no separate slot table needed).
        Index(
            "uq_doctor_slot_when_booked",
            "doctor_id",
            "start_time",
            unique=True,
            postgresql_where=text("status = 'booked'"),
        ),
    )