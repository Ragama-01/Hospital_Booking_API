from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from availability import generate_slots_for_doctor
from database import get_db
from models import Doctor
from schemas import AvailabilityResponse

router = APIRouter()


@router.get("/doctors/{doctor_id}/availability", response_model=AvailabilityResponse)
def get_doctor_availability(
    doctor_id: int,
    target_date: date = Query(..., alias="date", description="Date to check, e.g. 2026-08-25"),
    db: Session = Depends(get_db),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    slots = generate_slots_for_doctor(db, doctor, target_date)
    return AvailabilityResponse(doctor_id=doctor.id, date=target_date, available_slots=slots)