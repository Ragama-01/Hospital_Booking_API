from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import services
from database import get_db
from models import Patient
from schemas import (
    PatientAppointmentsResponse,
    PatientCreate,
    PatientResponse,
)

router = APIRouter()


@router.get("/patients", response_model=list[PatientResponse])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).order_by(Patient.patient_name).all()


@router.post(
    "/patients",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(
        patient_name=payload.patient_name,
        phone_number=payload.phone_number,
        email=payload.email,
    )
    db.add(patient)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A patient with this email already exists",
        )
    db.refresh(patient)
    return patient


@router.get("/patients/{patient_id}/appointments", response_model=PatientAppointmentsResponse)
def patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    patient, appointments = services.patient_appointments(db, patient_id)
    return PatientAppointmentsResponse(
        patient_id=patient.id, patient_name=patient.patient_name, appointments=appointments
    )