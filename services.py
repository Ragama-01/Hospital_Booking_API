"""Business logic for the clinic booking system.

Validation and mutation rules live here so the routers stay thin and the
booking logic is testable in isolation.
"""

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Appointment, AppointmentStatus, Doctor, Patient

SLOT_MINUTES = 30
# Appointments must be booked at least this far in the future (bonus rule).
MIN_BOOKING_LEAD_MINUTES = 60


def _slot_is_aligned(start: datetime) -> bool:
    """Slots must land on 30-minute boundaries (e.g. 09:00 or 09:30)."""
    return start.minute % SLOT_MINUTES == 0 and start.second == 0 and start.microsecond == 0


def validate_slot(db: Session, doctor: Doctor, slot_start: datetime) -> None:
    """Raise a 4xx error unless ``slot_start`` is a valid booking slot.

    Rules (in order) — must not be in the past / within an hour of now, must be
    30-minute aligned, must fit inside working hours, must not fall inside the
    break, and must not already be booked.
    """
    earliest = datetime.now() + timedelta(minutes=MIN_BOOKING_LEAD_MINUTES)
    if slot_start < earliest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Appointment must be at least "
                f"{MIN_BOOKING_LEAD_MINUTES} minutes in the future"
            ),
        )

    if not _slot_is_aligned(slot_start):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slots are only bookable at 30-minute boundaries (e.g. 09:00 or 09:30)",
        )

    slot_end = slot_start + timedelta(minutes=SLOT_MINUTES)
    if slot_start.time() < doctor.working_hours_start or slot_end.time() > doctor.working_hours_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot falls outside the doctor's working hours",
        )

    break_start = datetime.combine(slot_start.date(), doctor.break_start)
    break_end = datetime.combine(slot_start.date(), doctor.break_end)
    if slot_start < break_end and slot_end > break_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot falls within the doctor's break",
        )

    taken = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor.id,
            Appointment.start_time == slot_start,
            Appointment.status == AppointmentStatus.booked,
        )
        .first()
    )
    if taken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is already booked",
        )


def create_appointment(
    db: Session, doctor_id: int, patient_id: int, start_time: datetime, notes: str | None = None
) -> Appointment:
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    validate_slot(db, doctor, start_time)

    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        start_time=start_time,
        status=AppointmentStatus.booked,
        notes=notes,
    )
    db.add(appointment)
    # The PostgreSQL partial unique index on (doctor_id, start_time) where
    # status = 'booked' is a concurrency safety net; treat a race as a conflict.
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This time slot is already booked"
        )
    db.refresh(appointment)
    return appointment


def _get_appointment_or_404(db: Session, appointment_id: int) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appointment


def cancel_appointment(db: Session, appointment_id: int, reason: str) -> Appointment:
    appointment = _get_appointment_or_404(db, appointment_id)
    if appointment.status == AppointmentStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment is already cancelled",
        )
    appointment.status = AppointmentStatus.cancelled
    appointment.cancellation_reason = reason
    db.commit()
    db.refresh(appointment)
    return appointment


def reschedule_appointment(db: Session, appointment_id: int, new_start_time: datetime) -> Appointment:
    appointment = _get_appointment_or_404(db, appointment_id)
    if appointment.status == AppointmentStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reschedule a cancelled appointment",
        )

    # Reuse the same validation as a brand-new booking: the original slot is
    # freed automatically because we move the single row to the new start_time.
    validate_slot(db, appointment.doctor, new_start_time)

    appointment.start_time = new_start_time
    db.commit()
    db.refresh(appointment)
    return appointment


def patient_appointments(db: Session, patient_id: int) -> tuple[Patient, list[Appointment]]:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    now = datetime.now()
    appointments = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient_id, Appointment.start_time >= now)
        .order_by(Appointment.start_time.asc())
        .all()
    )
    return patient, appointments