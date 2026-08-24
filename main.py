from fastapi import FastAPI

from routers import appointments, doctors, patients

app = FastAPI(title="Clinic Booking System")


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "Clinic Booking System"}


app.include_router(doctors)
app.include_router(appointments)
app.include_router(patients)