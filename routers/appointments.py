from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import services
from database import get_db
from schemas import AppointmentCreate, AppointmentResponse, CancelRequest, RescheduleRequest

router = APIRouter()


@router.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    appointment = services.create_appointment(
        db, payload.doctor_id, payload.patient_id, payload.start_time, payload.notes
    )
    return appointment


@router.patch("/appointments/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int, payload: CancelRequest, db: Session = Depends(get_db)
):
    return services.cancel_appointment(db, appointment_id, payload.reason)


@router.patch("/appointments/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    appointment_id: int, payload: RescheduleRequest, db: Session = Depends(get_db)
):
    return services.reschedule_appointment(db, appointment_id, payload.new_start_time)