"use strict";

const $ = (sel) => document.querySelector(sel);

let TOKEN = null;
let CURRENT = null;

// ------------------------------------------------------------------ //
//  API helper
// ------------------------------------------------------------------ //
async function api(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (TOKEN) headers["Authorization"] = `Bearer ${TOKEN}`;
  if (opts.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";

  const res = await fetch(path, { ...opts, headers });
  if (res.status === 401) { logout(); throw new Error("Session expired"); }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error((data && data.detail) || res.statusText);
  return data;
}

// ------------------------------------------------------------------ //
//  Views & navigation
// ------------------------------------------------------------------ //
function showView(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("hidden", v.id !== `view-${name}`));
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
}

// ------------------------------------------------------------------ //
//  Login / logout
// ------------------------------------------------------------------ //
async function login(e) {
  e.preventDefault();
  const body = new URLSearchParams();
  body.append("username", $("#login-username").value.trim());
  body.append("password", $("#login-password").value);
  try {
    const res = await fetch("/auth/login", { method: "POST", body });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");
    TOKEN = data.access_token;
    CURRENT = data;
    $("#login-error").textContent = "";
    $("#login-view").classList.add("hidden");
    $("#dashboard").classList.remove("hidden");
    $("#user-chip").textContent = `👤 ${data.username} (${data.role})`;
    showView("overview");
    loadOverview();
  } catch (err) {
    $("#login-error").textContent = err.message;
  }
}

function logout() {
  TOKEN = null;
  $("#dashboard").classList.add("hidden");
  $("#login-view").classList.remove("hidden");
  $("#login-password").value = "admin123";
  $("#login-username").value = "admin";
}

// ------------------------------------------------------------------ //
//  Overview
// ------------------------------------------------------------------ //
async function loadOverview() {
  try {
    const s = await api("/reports/summary");
    $("#stat-cards").innerHTML = `
      <div class="stat"><div class="num">${s.total_patients}</div><div class="lbl">Patients</div></div>
      <div class="stat"><div class="num" style="color:var(--high)">${s.high_risk_count}</div><div class="lbl">High risk</div></div>
      <div class="stat"><div class="num" style="color:var(--moderate)">${s.moderate_risk_count}</div><div class="lbl">Moderate</div></div>
      <div class="stat"><div class="num" style="color:var(--low)">${s.low_risk_count}</div><div class="lbl">Low</div></div>
      <div class="stat"><div class="num">${s.average_age}</div><div class="lbl">Avg age</div></div>
      <div class="stat"><div class="num">${s.total_departments}</div><div class="lbl">Departments</div></div>`;

    const total = s.total_patients || 1;
    $("#risk-bar").innerHTML = `
      <div class="low" style="width:${(s.low_risk_count / total * 100).toFixed(1)}%">${s.low_risk_count}</div>
      <div class="mod" style="width:${(s.moderate_risk_count / total * 100).toFixed(1)}%">${s.moderate_risk_count}</div>
      <div class="high" style="width:${(s.high_risk_count / total * 100).toFixed(1)}%">${s.high_risk_count}</div>`;

    const patients = await api("/patients");
    const top = patients.slice(0, 8);
    $("#top-risk-table tbody").innerHTML = top.map((p) => rowHTML(p)).join("");
  } catch (err) { alert(err.message); }
}

// ------------------------------------------------------------------ //
//  Patients list
// ------------------------------------------------------------------ //
function riskBadge(label) {
  if (!label) return '<span class="badge b-LOW">—</span>';
  return `<span class="badge b-${label}">${label}</span>`;
}

function rowHTML(p) {
  return `<tr>
    <td>${p.patient_id}</td>
    <td><strong>${p.name}</strong></td>
    <td>${p.age}</td>
    <td>${p.gender}</td>
    <td>${p.blood_group}</td>
    <td>${riskBadge(p.risk_label)} ${p.risk_score}</td>
    <td><button class="btn btn-sm" onclick="openDetail('${p.patient_id}')">Details</button></td>
  </tr>`;
}

async function loadPatients() {
  try {
    const q = $("#patient-search").value.trim();
    const patients = await api(`/patients${q ? `?query=${encodeURIComponent(q)}` : ""}`);
    $("#patients-table tbody").innerHTML = patients.map(rowHTML).join("");
  } catch (err) { alert(err.message); }
}

// ------------------------------------------------------------------ //
//  Patient detail (risk card + vitals + visits + add reading)
// ------------------------------------------------------------------ //
async function openDetail(pid) {
  showView("add");
  $("#patient-detail-card").classList.remove("hidden");
  try {
    const [risk, pat] = await Promise.all([
      api(`/patients/${pid}/risk`),
      api(`/patients/${pid}`),
    ]);
    $("#pd-title").textContent = `🧑‍⚕️ ${risk.name} (${pid})`;

    const ml = risk.ml_probability != null
      ? `<div class="metric"><div class="k">ML probability</div><div class="v">${(risk.ml_probability * 100).toFixed(1)}% ${risk.ml_label ? riskBadge(risk.ml_label) : ""}</div></div>`
      : "<div class='metric'><div class='k'>ML</div><div class='v'>⚠ not trained</div></div>";

    const vitals = pat.vitals_history.length
      ? pat.vitals_history.map((v) =>
          `<li>${v.recorded_at.slice(0, 16).replace("T", " ")} — ${v.systolic}/${v.diastolic} mmHg, HR ${v.heart_rate}, ${v.temperature_c}°C</li>`).join("")
      : "<li>No readings yet</li>";
    const visits = pat.visits.length
      ? pat.visits.map((v) => `<li>${v.visit_date} — ${v.reason}${v.notes ? ` <em>(${v.notes})</em>` : ""}</li>`).join("")
      : "<li>No visits yet</li>";

    $("#pd-body").innerHTML = `
      <div class="detail-grid">
        <div class="card">
          <h3>Risk assessment</h3>
          <div class="metric-grid">
            <div class="metric"><div class="k">Rule score</div><div class="v">${risk.risk_score} ${riskBadge(risk.risk_label)}</div></div>
            ${ml}
            <div class="metric"><div class="k">BMI</div><div class="v">${risk.bmi} (${risk.bmi_category})</div></div>
            <div class="metric"><div class="k">Blood pressure</div><div class="v">${risk.bp_category}</div></div>
            <div class="metric"><div class="k">Fever</div><div class="v">${risk.has_fever ? "Yes" : "No"}</div></div>
          </div>
          <h3 style="margin-top:1rem">Add reading</h3>
          <form id="vitals-form" class="f-row" style="grid-template-columns:repeat(auto-fit,minmax(110px,1fr))">
            <input type="number" placeholder="Systolic" id="v-sys" min="40" max="300">
            <input type="number" placeholder="Diastolic" id="v-dia" min="20" max="200">
            <input type="number" placeholder="Heart rate" id="v-hr" min="20" max="250">
            <input type="number" step="0.1" placeholder="Temp °C" id="v-temp" min="30" max="45">
            <button class="btn btn-primary" type="submit">Save</button>
          </form>
        </div>
        <div>
          <div class="card"><h3>Vitals history</h3><ul class="tree">${vitals}</ul></div>
          <div class="card"><h3>Visits</h3><ul class="tree">${visits}</ul></div>
          <div class="card">
            <h3>Log a visit</h3>
            <form id="visit-form" class="f-row" style="grid-template-columns:1fr">
              <input type="text" placeholder="Reason (e.g. Fever)" id="v-reason">
              <button class="btn btn-primary" type="submit">Log visit</button>
            </form>
          </div>
        </div>
      </div>`;

    $("#vitals-form").onsubmit = async (e) => {
      e.preventDefault();
      const body = {
        systolic: +$("#v-sys").value || 120,
        diastolic: +$("#v-dia").value || 80,
        heart_rate: +$("#v-hr").value || 72,
        temperature_c: +$("#v-temp").value || 36.6,
      };
      const el = document.createElement("input"); el.type = "hidden";
      try { await api(`/patients/${pid}/vitals`, { method: "POST", body: JSON.stringify(body) }); openDetail(pid); }
      catch (err) { alert(err.message); }
    };
    $("#visit-form").onsubmit = async (e) => {
      e.preventDefault();
      try { await api(`/patients/${pid}/visits`, { method: "POST", body: JSON.stringify({ reason: $("#v-reason").value }) }); openDetail(pid); }
      catch (err) { alert(err.message); }
    };
  } catch (err) { alert(err.message); }
}

// ------------------------------------------------------------------ //
//  Add patient
// ------------------------------------------------------------------ //
$("#add-form").onsubmit = async (e) => {
  e.preventDefault();
  const body = {
    name: $("#a-name").value,
    dob: $("#a-dob").value,
    gender: $("#a-gender").value,
    blood_group: $("#a-blood").value.trim(),
    height_cm: +$("#a-height").value || 0,
    weight_kg: +$("#a-weight").value || 0,
    allergies: $("#a-allergies").value.split(",").map((s) => s.trim()).filter(Boolean),
  };
  try {
    const p = await api("/patients", { method: "POST", body: JSON.stringify(body) });
    $("#add-msg").textContent = `✅ Added ${p.name} with ID ${p.patient_id}`;
    e.target.reset();
    openDetail(p.patient_id);
  } catch (err) { $("#add-msg").textContent = "❌ " + err.message; $("#add-msg").className = "error"; }
};

// ------------------------------------------------------------------ //
//  ML model page
// ------------------------------------------------------------------ //
async function loadML() {
  try {
    const s = await api("/ml/status");
    if (!s.model_available) {
      $("#ml-card").innerHTML = `<p>⚠ No model artifact found. Train it with:</p><pre>uv run python -m ml.train</pre>`;
      return;
    }
    const models = Object.entries(s.metrics).map(([name, m]) =>
      `<div class="card"><h3>${name.replace("_", " ").toUpperCase()}</h3><div class="metric-grid">` +
      Object.entries(m).map(([k, v]) => `<div class="metric"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("") +
      `</div></div>`).join("");
    const imp = Object.entries(s.feature_importance).sort((a, b) => b[1] - a[1])
      .map(([f, v]) => `<li>${f}: <strong>${v}</strong></li>`).join("");

    $("#ml-card").innerHTML = `
      <p>Best model: <strong>${s.best_model}</strong> (ROC-AUC ${s.metrics[s.best_model].roc_auc})</p>
      ${models}
      <h3>Feature importance</h3><ul class="tree">${imp}</ul>`;
  } catch (err) { alert(err.message); }
}

// ------------------------------------------------------------------ //
//  Departments
// ------------------------------------------------------------------ //
async function loadDepartments() {
  try {
    const d = await api("/reports/departments");
    $("#dept-count").textContent = `(${d.total} total)`;
    $("#dept-tree").innerHTML = "<ul class='tree'>" + d.tree.map((t) => `<li>${t}</li>`).join("") + "</ul>";
  } catch (err) {
    $("#dept-tree").innerHTML = `<p class="error">${err.message} — admin role required.</p>`;
  }
}

// ------------------------------------------------------------------ //
//  Wire-up
// ------------------------------------------------------------------ //
$("#login-form").onsubmit = login;
$("#btn-logout").onclick = logout;

document.querySelectorAll(".nav-btn").forEach((b) =>
  b.addEventListener("click", () => {
    showView(b.dataset.view);
    if (b.dataset.view === "patients") loadPatients();
    if (b.dataset.view === "ml") loadML();
    if (b.dataset.view === "departments") loadDepartments();
  })
);

let searchTimer = null;
$("#patient-search").addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadPatients, 250);
});