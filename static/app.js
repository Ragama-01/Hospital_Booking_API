"use strict";

const $ = (id) => document.getElementById(id);

const state = {
  doctors: [],
  patients: [],
  selectedSlot: null,
};

const toastEl = $("toast");
let toastTimer = null;

function toast(msg, type = "success") {
  toastEl.textContent = msg;
  toastEl.className = `toast show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.className = "toast";
  }, 3200);
}

async function api(path, options = {}) {
  let res;
  try {
    res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("Could not reach the server. Is it running?");
  }
  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    const detail = data && (data.detail || data.message);
    if (typeof detail === "string") throw new Error(detail);
    throw new Error(JSON.stringify(detail || data || "Request failed"));
  }
  return data;
}

/* ---------- UI helpers ---------- */

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[ch]));
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

function toDateInputValue(date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

function fmtTime(t) {
  return String(t).slice(0, 5); // "09:00:00" -> "09:00"
}

function fmtDateTime(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString([], {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Slots must begin at least 1 hour from now (mirrors the backend rule).
function filterEligibleSlots(slots, dateStr) {
  const earliest = new Date(Date.now() + 60 * 60 * 1000);
  return slots.filter((slot) => {
    const [h, m] = String(slot).slice(0, 5).split(":").map(Number);
    const slotDate = new Date(`${dateStr}T${pad2(h)}:${pad2(m)}`);
    return slotDate >= earliest;
  });
}

/* ---------- Data loading ---------- */

async function loadDoctors() {
  state.doctors = await api("/doctors");
  populateSpecialities();
  filterDoctors();
}

function populateSpecialities() {
  const specs = [...new Set(state.doctors.map((d) => d.speciality))].sort();
  const sel = $("speciality-select");
  sel.innerHTML = '<option value="">Select a speciality</option>';
  specs.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    sel.appendChild(opt);
  });
  if (!specs.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No doctors available";
    sel.appendChild(opt);
  }
}

function filterDoctors() {
  const spec = $("speciality-select").value;
  const sel = $("doctor-select");
  sel.innerHTML = "";
  if (!spec) {
    sel.disabled = true;
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "Select a speciality first";
    sel.appendChild(opt);
    return;
  }
  const doctors = state.doctors.filter((d) => d.speciality === spec);
  sel.disabled = false;
  doctors.forEach((doc) => {
    const opt = document.createElement("option");
    opt.value = doc.id;
    opt.textContent = doc.full_name;
    sel.appendChild(opt);
  });
  if (!doctors.length) {
    sel.disabled = true;
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No doctors in this speciality";
    sel.appendChild(opt);
  }
}

async function loadPatients() {
  state.patients = await api("/patients");
  ["patient-select", "my-patient"].forEach((id) => {
    const sel = $(id);
    const prev = sel.value;
    sel.innerHTML = '<option value="">Select a patient</option>';
    state.patients.forEach((pat) => {
      const opt = document.createElement("option");
      opt.value = pat.id;
      opt.textContent = `${pat.patient_name} \u00b7 ${pat.email}`;
      sel.appendChild(opt);
    });
    if (prev) sel.value = prev;
  });
}
/* ---------- Slots (booking) ---------- */

function renderSlots(slots) {
  const wrap = $("slots");
  const info = $("slots-info");
  wrap.innerHTML = "";
  if (!slots.length) {
    info.textContent =
      "No bookable slots for this doctor/date (all taken, outside hours, " +
      "or within the next hour). Try a later date.";
    return;
  }
  info.textContent =
    `${slots.length} available slot${slots.length === 1 ? "" : "s"}. ` +
    "Slots starting within the next hour are hidden.";
  slots.forEach((slot) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.textContent = fmtTime(slot);
    btn.addEventListener("click", () => {
      wrap.querySelectorAll(".chip").forEach((x) => x.classList.remove("selected"));
      btn.classList.add("selected");
      state.selectedSlot = slot;
    });
    wrap.appendChild(btn);
  });
}

async function loadSlots() {
  const doctorId = $("doctor-select").value;
  const date = $("date-input").value;
  if (!doctorId || !date) {
    toast("Please pick a speciality, doctor and date.", "error");
    return;
  }
  try {
    const data = await api(`/doctors/${doctorId}/availability?date=${date}`);
    renderSlots(filterEligibleSlots(data.available_slots, date));
    $("slots-wrap").classList.remove("hidden");
  } catch (err) {
    toast(err.message, "error");
  }
}

function clearSlots() {
  state.selectedSlot = null;
  $("slots").innerHTML = "";
  $("slots-info").textContent = "";
  $("slots-wrap").classList.add("hidden");
}

/* ---------- New patient ---------- */

async function createPatient() {
  const name = $("np-name").value.trim();
  const phone = $("np-phone").value.trim();
  const email = $("np-email").value.trim();
  if (!name || !phone || !email) {
    toast("Please fill in name, phone and email.", "error");
    return;
  }
  try {
    const created = await api("/patients", {
      method: "POST",
      body: JSON.stringify({ patient_name: name, phone_number: phone, email }),
    });
    await loadPatients();
    $("patient-select").value = created.id;
    $("new-patient").classList.add("hidden");
    $("np-name").value = $("np-phone").value = $("np-email").value = "";
    toast(`Registered ${created.patient_name}.`);
  } catch (err) {
    toast(err.message, "error");
  }
}

/* ---------- Booking submit ---------- */

async function submitBooking(event) {
  event.preventDefault();
  const doctorId = Number($("doctor-select").value);
  const patientId = Number($("patient-select").value);
  const date = $("date-input").value;
  if (!doctorId) return toast("Select a doctor.", "error");
  if (!patientId) return toast("Select a patient.", "error");
  if (!state.selectedSlot) return toast("Select a time slot.", "error");
  const start_time = `${date}T${fmtTime(state.selectedSlot)}:00`;
  const notes = $("notes-input").value.trim() || null;
  try {
    await api("/appointments", {
      method: "POST",
      body: JSON.stringify({
        doctor_id: doctorId,
        patient_id: patientId,
        start_time,
        notes,
      }),
    });
    toast("Appointment booked successfully.");
    state.selectedSlot = null;
    $("slots").querySelectorAll(".chip.selected").forEach((x) => x.classList.remove("selected"));
    $("notes-input").value = "";
  } catch (err) {
    toast(err.message, "error");
  }
}
/* ---------- Appointments view ---------- */

async function loadAppointments() {
  const patientId = Number($("my-patient").value);
  if (!patientId) return toast("Select a patient.", "error");
  const list = $("appointments-list");
  try {
    const data = await api(`/patients/${patientId}/appointments`);
    list.innerHTML = "";
    if (!data.appointments.length) {
      list.innerHTML = '<p class="muted">No upcoming appointments for this patient.</p>';
      return;
    }
    data.appointments.forEach((appt) => {
      const doc = state.doctors.find((d) => d.id === appt.doctor_id);
      list.appendChild(renderAppointmentCard(appt, doc));
    });
  } catch (err) {
    toast(err.message, "error");
  }
}

function renderAppointmentCard(appt, doc) {
  const card = document.createElement("article");
  card.className = "appointment-card";
  const docName = doc
    ? `${doc.full_name} (${doc.speciality})`
    : `Doctor #${appt.doctor_id}`;
  const statusClass = appt.status === "booked" ? "booked" : "cancelled";

  card.innerHTML =
    `<div class="appt-head">
      <div>
        <div class="appt-time">${fmtDateTime(appt.start_time)}</div>
        <div class="appt-doctor">${escapeHtml(docName)}</div>
      </div>
      <span class="badge ${statusClass}">${escapeHtml(appt.status)}</span>
    </div>` +
    (appt.notes ? `<p class="appt-notes">Notes: ${escapeHtml(appt.notes)}</p>` : "") +
    (appt.cancellation_reason
      ? `<p class="appt-cancel-reason">Cancelled: ${escapeHtml(appt.cancellation_reason)}</p>`
      : "") +
    '<div class="appt-actions"></div>' +
    '<div class="appt-inline hidden"></div>';

  if (appt.status === "booked") {
    const actions = card.querySelector(".appt-actions");
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "btn btn-ghost";
    cancel.textContent = "Cancel";
    cancel.addEventListener("click", () => beginCancel(card, appt));
    const reschedule = document.createElement("button");
    reschedule.type = "button";
    reschedule.className = "btn btn-ghost";
    reschedule.textContent = "Reschedule";
    reschedule.addEventListener("click", () => beginReschedule(appt));
    actions.append(cancel, reschedule);
  }
  return card;
}

function beginCancel(card, appt) {
  const area = card.querySelector(".appt-inline");
  area.classList.remove("hidden");
  area.innerHTML =
    '<input type="text" placeholder="Reason for cancellation" />' +
    '<div class="row">' +
    '<button type="button" class="btn btn-danger">Confirm cancel</button>' +
    '<button type="button" class="btn btn-ghost">Dismiss</button>' +
    "</div>";
  const buttons = [...area.querySelectorAll("button")];
  const [confirm, dismiss] = buttons;
  confirm.addEventListener("click", async () => {
    const reason = area.querySelector("input").value.trim();
    if (!reason) return toast("Enter a cancellation reason.", "error");
    try {
      await api(`/appointments/${appt.id}/cancel`, {
        method: "PATCH",
        body: JSON.stringify({ reason }),
      });
      toast("Appointment cancelled.");
      await loadAppointments();
    } catch (err) {
      toast(err.message, "error");
    }
  });
  dismiss.addEventListener("click", () => {
    area.classList.add("hidden");
    area.innerHTML = "";
  });
}
/* ---------- Reschedule modal ---------- */

function closeModal() {
  $("modal").classList.add("hidden");
}

async function beginReschedule(appt) {
  const doc = state.doctors.find((d) => d.id === appt.doctor_id);
  const dateStr = toDateInputValue(new Date(appt.start_time));
  $("modal-title").textContent = "Reschedule appointment";
  $("modal-sub").textContent =
    `${doc ? doc.full_name : "Doctor"} \u00b7 ${fmtDateTime(appt.start_time)}`;
  $("modal").classList.remove("hidden");

  const slotWrap = $("modal-slots");
  slotWrap.innerHTML = '<p class="muted">Loading…</p>';
  try {
    const data = await api(`/doctors/${appt.doctor_id}/availability?date=${dateStr}`);
    const slots = filterEligibleSlots(data.available_slots, dateStr);
    slotWrap.innerHTML = "";
    if (!slots.length) {
      slotWrap.innerHTML =
        '<p class="muted">No alternative slots on this date (all taken or within the next hour).</p>';
    }
    slots.forEach((slot) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.textContent = fmtTime(slot);
      btn.addEventListener("click", async () => {
        const new_start_time = `${dateStr}T${fmtTime(slot)}:00`;
        try {
          await api(`/appointments/${appt.id}/reschedule`, {
            method: "PATCH",
            body: JSON.stringify({ new_start_time }),
          });
          closeModal();
          toast("Appointment rescheduled.");
          await loadAppointments();
        } catch (err) {
          toast(err.message, "error");
        }
      });
      slotWrap.appendChild(btn);
    });
  } catch (err) {
    slotWrap.innerHTML = "";
    toast(err.message, "error");
  }
}

/* ---------- Tabs ---------- */

function setupTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const view = tab.dataset.view;
      $("view-book").classList.toggle("hidden", view !== "book");
      $("view-appointments").classList.toggle("hidden", view !== "appointments");
    });
  });
}

/* ---------- Init ---------- */

function initDate() {
  const input = $("date-input");
  const today = toDateInputValue(new Date());
  input.min = today;
  input.value = today;
}

(async function init() {
  initDate();
  $("speciality-select").addEventListener("change", () => {
    filterDoctors();
    clearSlots();
  });
  $("load-slots").addEventListener("click", loadSlots);
  $("toggle-new-patient").addEventListener("click", () => {
    $("new-patient").classList.toggle("hidden");
  });
  $("create-patient").addEventListener("click", createPatient);
  $("booking-form").addEventListener("submit", submitBooking);
  $("load-appointments").addEventListener("click", loadAppointments);
  $("modal-close").addEventListener("click", closeModal);
  $("modal").addEventListener("click", (e) => {
    if (e.target === $("modal")) closeModal();
  });
  setupTabs();

  try {
    await Promise.all([loadDoctors(), loadPatients()]);
  } catch (err) {
    toast(err.message, "error");
  }
})();