from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import services
from database import get_db
from schemas import PatientAppointmentsResponse

router = APIRouter()


@router.get("/patients/{patient_id}/appointments", response_model=PatientAppointmentsResponse)
def patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    patient, appointments = services.patient_appointments(db, patient_id)
    return PatientAppointmentsResponse(
        patient_id=patient.id, patient_name=patient.patient_name, appointments=appointments
    )