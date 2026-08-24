from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class AvailabilityResponse(BaseModel):
    doctor_id: int
    date: date
    available_slots: list[time]


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: datetime
    notes: str | None = None


class CancelRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Reason for cancellation")


class RescheduleRequest(BaseModel):
    new_start_time: datetime


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    patient_id: int
    start_time: datetime
    status: str
    cancellation_reason: str | None = None
    notes: str | None = None


class PatientAppointmentsResponse(BaseModel):
    patient_id: int
    patient_name: str
    appointments: list[AppointmentResponse]


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    speciality: str
    phone_number: str
    email: str
    working_hours_start: time
    working_hours_end: time
    break_start: time
    break_end: time


class PatientCreate(BaseModel):
    patient_name: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_name: str
    phone_number: str
    email: str