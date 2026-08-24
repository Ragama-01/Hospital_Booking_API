
 1. Overview

This document outlines the key assumptions made during the design of the clinic appointment booking system and explains the technical decisions behind the tools and technologies selected for development and deployment.

The purpose of documenting these decisions is to clearly define the expected behavior of the system, establish the boundaries of the initial implementation, and provide a rationale for the technology choices.

The system is designed as an initial version that can be demonstrated within the available development timeline while maintaining a structure that can be expanded as the clinic's requirements grow.

---

2. Design Assumptions

The following assumptions have been made about how the clinic operates and how the appointment system is expected to function.

 2.1 Clinic Operating Hours

The clinic operates during regular daytime hours, but the system does not rely on a
single hard-coded opening and closing time. Instead, each doctor has **working hours**
stored on their record, and appointments are only allowed within the selected
doctor's individual working hours (see 2.4 and 2.5).

Appointments outside a doctor's working hours are not considered valid.

This per-doctor schedule also provides a defined window that is used when generating
available appointment slots.

---

 2.2 Patient and Doctor Registration

In the current version, patients register using their name, phone number, and email
when they make a booking. No password or login is required. Each booking is recorded
against the matching patient — matched by email, or created automatically if the
email is not yet registered.

Doctors, on the other hand, are pre-seeded into the system by the clinic; there is no
self-service doctor registration. Each doctor record stores their specialty, working
hours, and break period.

Role-based authentication and login are not part of this first version and are
planned as future enhancements (see Section 2.8). The schema is modelled so that
roles such as patient, doctor, and administrator can be added later without
rebuilding the system.

---

 2.3 Doctor Specialties

Doctors are assumed to have specific medical specialties.

For the initial version of the system, the clinic will have **five specialties**, with one doctor assigned to each specialty.

The five specialties will represent some of the clinic's most commonly requested services.

This approach keeps the initial implementation manageable while still demonstrating the core functionality of specialty-based appointment booking.

The system can later be expanded to support:

* Multiple doctors within the same specialty
* Additional specialties
* Doctors with multiple specialties
* Different appointment durations based on specialty

The one-doctor-per-specialty assumption is therefore a limitation of the initial version rather than a permanent system restriction.

---

 2.4 Appointment Scheduling

Appointments will be scheduled based on:

* Clinic operating hours
* Doctor availability
* Existing appointments
* Doctor break periods

The system should prevent conflicting appointments from being booked for the same doctor at the same time.

This ensures that a doctor cannot be assigned to multiple appointments during the same time slot.

---

 2.5 Doctor Break Period

Each doctor is assumed to have a **one-hour break** during the clinic's operating hours.

The break time is selected by the individual doctor.

The appointment scheduling logic must therefore take the doctor's break into consideration when determining available appointment slots.

For example, if a doctor chooses to take a break from 1:00 PM to 2:00 PM, the system should not make that period available for appointment booking.

This also allows different doctors to have different break schedules.

---

 2.6 Cancelled and Rescheduled Appointments

Cancelled and rescheduled appointments will not simply be discarded.

The system will retain relevant appointment history so that the clinic can use this information for:

* Operational planning
* Identifying appointment trends
* Understanding cancellation patterns
* Understanding rescheduling patterns
* Future decision-making
* Improving resource allocation

For example, historical cancellation data could eventually help the clinic identify periods with unusually high cancellation rates.

Keeping this information also provides a foundation for future reporting and analytics functionality.

---

 2.7 Child Appointments and Age Restrictions

The system will assume that users making appointments for children must have an adult responsible for the booking.

If the appointment is being made for a child, the adult should make the appointment and provide relevant information in the **notes section**.

The initial system will therefore not require the child to independently create an account or book an appointment.

This approach simplifies the first version of the system while providing a clear mechanism for handling appointments involving minors.

A future version could introduce a dedicated guardian/parent relationship within the database if the clinic requires more detailed management of child patients.

---

 2.8 Initial Scope vs Future Expansion

The assumptions above are primarily intended to keep the first version of the system focused and achievable within the available development timeline.

Some of the current limitations are expected to change as the system develops.

Potential future enhancements include:

* Multiple doctors per specialty
* More than five specialties
* Administrator accounts
* Guardian/parent accounts
* Automated appointment reminders
* Email or SMS notifications
* More advanced reporting
* Doctor availability management
* Variable appointment durations
* Online payments
* Prescription or medical-record functionality
* More advanced analytics

The current design should therefore avoid unnecessarily restricting the database or application architecture in ways that would make these future additions difficult.

---

# 3. Technical Decisions

## 3.1 Technology Stack

The initial system will use the following technology stack:

| Component            | Technology |
| -------------------- | ---------- |
| Backend Framework    | FastAPI    |
| Programming Language | Python     |
| Database             | PostgreSQL |
| Deployment Platform  | Railway    |

The selected technologies provide a relatively lightweight development stack while still offering the ability to scale the application as the clinic's requirements increase.

---

 4. Backend Framework: FastAPI

 Decision

The backend API will be developed using **FastAPI**.

Reasons for Choosing FastAPI

 4.1 Fast Development

FastAPI allows APIs to be developed quickly using Python.

Given the available development timeline, choosing a framework that allows the core functionality to be implemented efficiently is important.

The goal is to prioritize a working and understandable system rather than introduce unnecessary complexity.

 4.2 Familiarity with Python

Python is a language that I am comfortable working with.

Using a familiar programming language reduces the amount of time required to learn new concepts while developing the system.

This allows more time to be spent on implementing and testing the actual clinic functionality.

 4.3 Easier Debugging and Explanation

Since the project needs to be developed within a limited timeframe, using technologies that I understand well reduces the likelihood of introducing unnecessary errors.

It also means that I will be in a better position to explain:

* How the API works
* How the web UI interacts with the API
* How appointments are created
* How appointment availability is calculated
* How the backend communicates with the database
* Why particular design decisions were made

 4.4 API-Oriented Architecture

FastAPI is well suited for building REST APIs.

This provides a clean separation between the backend and the frontend.

The backend exposes endpoints for:

* Listing doctors and checking a doctor's available slots
* Registering a patient and listing patients
* Booking an appointment
* Cancelling an appointment
* Rescheduling an appointment
* Viewing a patient's upcoming appointments

This architecture also makes it easier to introduce a different frontend in the future without having to completely redesign the backend.

---

 5. Database: PostgreSQL

 Decision

The system will use **PostgreSQL** as its relational database.

 Reasons for Choosing PostgreSQL

 5.1 Relational Database Structure

The clinic system contains several entities that have clear relationships with one another.

For example:

* Patients have appointments.
* Doctors have specialties.
* Doctors have appointments.
* Appointments have statuses.
* Appointments have scheduled dates and times.

A relational database is therefore appropriate for representing these relationships while maintaining data integrity.

 5.2 Compatibility with FastAPI

PostgreSQL works well with Python-based backend applications and can be integrated effectively with FastAPI.

This provides a reliable combination for building the application's data layer.

 5.3 Scalability

The clinic is considering expanding the platform in the future.

PostgreSQL provides a strong foundation for this expansion because it can handle a larger number of records and more complex relationships as the system grows.

The database can therefore support future additions such as:

* More doctors
* More patients
* More specialties
* Multiple clinic branches
* Appointment history
* Reporting
* Additional healthcare-related modules

 5.4 Familiarity

PostgreSQL is also a database technology that I am already familiar with.

Using a database I understand reduces development time and makes it easier to troubleshoot database-related problems.

It also allows me to focus on designing the clinic system rather than spending significant time learning an unfamiliar database technology.

---

 6. Deployment: Railway

 Decision

The initial application is deployed using **Railway**, which also provisions a
managed PostgreSQL database for production.

 Reasons for Choosing Railway

 6.1 Suitable for an Initial Deployment

The project is initially being developed as a demonstration/prototype with the possibility of becoming a larger production system later.

Railway provides a practical option for deploying the application without requiring a complex infrastructure setup at the beginning.

 6.2 Cost Considerations

Cost is an important consideration for the initial version of the project.

The deployment platform should allow the application to be hosted without introducing unnecessary infrastructure costs during the early development and testing stages.

 6.3 Future Growth

The deployment approach should also leave room for the system to grow.

As the clinic platform expands, the deployment architecture can be reviewed and adjusted based on:

* Number of users
* Database size
* Traffic
* Availability requirements
* Performance requirements
* Operational costs

The initial deployment choice should therefore be viewed as appropriate for the current stage of the project rather than a permanent infrastructure decision.

---

 7. Overall Design Philosophy

The overall design approach is based on three main principles:

 7.1 Keep the Initial Version Manageable

The system should implement the core clinic appointment functionality without introducing unnecessary complexity.

The initial scope includes the essential workflow of:

**Patient Registration → Doctor/Specialty Selection → Appointment Booking → Appointment Management**

 7.2 Build With Future Expansion in Mind

Although the initial implementation is intentionally limited, the database and backend should be structured so that additional functionality can be introduced later without requiring the entire system to be rebuilt.

 7.3 Prioritize Understanding and Reliability

The selected technologies are technologies that I am sufficiently familiar with to develop, debug, test, and explain confidently within the available timeline.

This is an intentional design decision.

For this project, a smaller and well-understood technology stack is preferable to using more complex technologies simply because they are available.

---

# 8. Summary of Key Decisions

| Area                       | Decision                                              | Reason                                                         |
| -------------------------- | ----------------------------------------------------- | -------------------------------------------------------------- |
| Clinic Hours               | Per-doctor working hours (configured per doctor)      | Defines the appointment scheduling window                      |
| Authentication             | Not in v1 — patients register with name/phone/email   | Role-based login planned for a future version                  |
| Specialties                | Five initial specialties                              | Keeps the initial implementation manageable                    |
| Doctors                    | One doctor per specialty initially                    | Simplifies scheduling and demonstrates specialty-based booking |
| Breaks                     | One-hour break per doctor                             | Reflects doctor availability                                   |
| Cancelled/Rescheduled Data | Retained                                              | Supports planning, analysis, and future decision-making        |
| Child Appointments         | Adult makes the booking and provides details in notes | Handles minors without requiring child accounts                |
| Backend                    | FastAPI + Python                                      | Fast development, familiarity, clear API structure             |
| Database                   | PostgreSQL                                            | Relational structure, scalability, compatibility, familiarity  |
| Deployment                 | Railway                                               | Practical initial deployment with future growth in mind        |

---

# 9. Deployment URL, Branch & CI/CD Pipeline

## 9.1 Handling Ambiguous Requirements

When a requirement was ambiguous or underspecified, a decision was made and
recorded rather than leaving the behavior undefined. Each such decision is
documented in Section 2 (Design Assumptions) and summarized in Section 8. For
example:

* The clinic's operating hours were interpreted as **per-doctor working hours**
  stored on each doctor record, rather than a single hard-coded window.
* Registration was scoped to **patients only** (name, phone, email); login and
  role-based access were recorded as future enhancements rather than silently
  assuming authentication existed.

This policy ensures the expected behavior of the system is explicit and
reviewable.

 9.2 Public URL of the Deployed Application

The live application is deployed to Railway and is available at:

> https://hospitalbookingapi-production.up.railway.app/


 9.3 Which Branch Triggers a Deployment and How

* **Repository:** `https://github.com/Ragama-01/Hospital_Booking_API`
* **Branch:** `main`
* **Trigger:** a push (or merge) to `main` automatically starts a new Railway
  deployment.

How it works: the Railway service is connected to the GitHub repository and
watches the `main` branch. When new commits are pushed to `main`, Railway pulls
the latest code and creates a new deployment. No manual step is required — the
pipeline is automatic on every push to `main`.

 9.4 What the Deployment Pipeline Does

Railway builds the project using Nixpacks (its default Python builder) and then
runs the command defined in the `Procfile`:

```text
web: python startup.py && uvicorn main:app --host 0.0.0.0 --port $PORT
```

On each deployment, the pipeline:

1. **Installs dependencies** from `requirements.txt` (FastAPI, Uvicorn,
   SQLAlchemy, psycopg2, Pydantic).
2. **Runs `python startup.py`**, which:
   * creates the database tables if they do not already exist, and
   * seeds the 5 doctors (and 5 dummy patients) if the tables are empty —
     both steps are idempotent.
3. **Starts the server** with Uvicorn, binding to `0.0.0.0` on Railway's
   injected `$PORT`, serving both the API and the static web UI.

The database connection is provided by Railway's managed PostgreSQL, resolved at
runtime through the `RAILWAY_DATABASE_URL` / `DATABASE_URL` / `PG*` environment
variables. On every deploy, the database tables and seed data are guaranteed to
exist before the server starts serving requests.

---

 10. AI Reflection

1.What did I use AI for across the four sections- I used AI for testing, Designing my front end, redefining my read me file as well debugging the errors I encountered (i majorly use cline extension on vs code)

2.Examples of where Ai improved my work - Ai helped me to be elaborate as possible and stay within the required scope and identify fine print that I could have missed 

3.What did I prompt it with - "I have a code base and Postgres db design for a clinic Booking System. It's in initial phase and with a chance of expansion. It currently has five doctors each with their own specialty. In my Code base help me identify if I'm within scope and if there's something I'm missing." In addition to this I added section one instructions

4. An example where it was wrong - In the UI it provided a text field to select a patient which wasn't necessary in the booking appointment.

5. I caught when I was inputting dummy data to ensure it was ok
 
6. What I used my own judgement instead of AI - My DB design and tools I needed to use . I have worked with theses tools therefore I was sure i was comfortable handling this bit on my own.




 11. Conclusion

The design decisions for the clinic appointment system are intended to balance **functionality, development speed, reliability, maintainability, and future scalability**.

The initial version deliberately keeps the scope focused by limiting the number of specialties and doctors while still implementing the fundamental appointment-management workflow.

FastAPI, PostgreSQL, and Railway were selected because they provide a straightforward technology stack that can be implemented effectively within the available timeline while leaving room for the platform to expand.

The assumptions documented in this file should be treated as the baseline requirements for the initial version of the system. As the clinic's requirements become clearer, these assumptions can be reviewed and updated rather than being treated as permanent restrictions.
