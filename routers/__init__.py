"""API routers for the clinic booking system."""

from .appointments import router as appointments
from .doctors import router as doctors
from .patients import router as patients

__all__ = ["appointments", "doctors", "patients"]