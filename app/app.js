/* =========================================================
   SIPHER Personas – App Logic
   ========================================================= */

const API_BASE = "http://localhost:8000";

// Read ?test=true from the page URL
const IS_TEST = new URLSearchParams(window.location.search).get("test") === "true";

// Append &test=true to every API path when in test mode
function apiPath(path) {
  if (!IS_TEST) return path;
  const sep = path.includes("?") ? "&" : "?";
  return path + sep + "test=true";
}

const GROUP_COLORS = {
  "Employed":        "#3b82f6",
  "Self-employed":   "#8b5cf6",
  "Retired":         "#f59e0b",
  "Unemployed":      "#ef4444",
  "Student":         "#10b981",
  "LT sick/disabled":"#f97316",
  "Other":           "#6b7280",
};

// Numeric stats to show on cards (key = column name, label = display label, unit = suffix)
const STATS = [
  { key: "Derived age at interview",            label: "Avg. age",            unit: " yrs",  round: 1 },
  { key: "Monthly net pay (take-home)",         label: "Monthly take-home",   unit: "",      fmt: "currency" },
  { key: "Mental health score (SF-12 MCS)",     label: "Mental health",       unit: "/100",  round: 1 },
  { key: "Physical health score (SF-12 PCS)",   label: "Physical health",     unit: "/100",  round: 1 },
  { key: "Social class (NS-SEC 8)",             label: "Social class",        unit: "",      round: 1 },
  { key: "Household size",                      label: "Household size",      unit: "",      round: 1 },
  { key: "Number of children in household",     label: "Children",            unit: "",      round: 1 },
  { key: "Minutes spent travelling to work",    label: "Commute",             unit: " min",  round: 0 },
  { key: "Miles driven in last 12 months",      label: "Miles/year",          unit: "",      fmt: "number", round: 0 },
  { key: "Highest qualification",               label: "Avg. qual level",     unit: "",      round: 1 },
];

const FLAG_COLS = ["Employed", "Unemployed", "Retired", "Full-time student", "LT sick/disabled"];

// ----- State -----
let currentLa   = null;
let currentGroup = "All";
let allPersonas  = [];

// ----- DOM refs -----
const laSelect    = document.getElementById("la-select");
const tabContainer = document.getElementById("group-tabs");
const mainEl      = document.getElementById("main-content");
const summaryEl   = document.getElementById("summary-bar");

// ----- Boot -----
async function init() {
  // Show test-mode banner if ?test=true
  if (IS_TEST) {
    const banner = document.createElement("div");
    banner.id = "test-banner";
    banner.textContent = "⚠️ TEST MODE — showing data_test/ output";
    document.body.prepend(banner);
  }

  renderState("loading", "Loading Local Authorities…");
  try {
    const las = await apiFetch(apiPath("/las"));
    populateLaSelect(las);
  } catch (e) {
    renderState("error", `Could not reach API at ${API_BASE}. Is it running?<br><code>uvicorn api.main:app --reload</code>`);
  }
}

function populateLaSelect(las) {
  laSelect.innerHTML = '<option value="">— Select a Local Authority —</option>';
  las.forEach(({ code, name }) => {
    const opt = document.createElement("option");
    opt.value = code;
    opt.textContent = `${name} (${code})`;
    laSelect.appendChild(opt);
  });
  laSelect.disabled = false;
  renderState("empty", "Select a Local Authority above to explore its personas.");
}

laSelect.addEventListener("change", async () => {
  const code = laSelect.value;
  if (!code) { renderState("empty", "Select a Local Authority above."); return; }
  currentLa    = code;
  currentGroup = "All";
  renderState("loading", "Loading personas…");
  try {
    allPersonas = await apiFetch(apiPath(`/la/${code}/personas`));
    buildGroupTabs();
    renderPersonas();
  } catch (e) {
    renderState("error", `Failed to load personas for ${code}: ${e.message}`);
  }
});

// ----- Group tabs -----
function buildGroupTabs() {
  const groups = [...new Set(allPersonas.map(p => p.group).filter(Boolean))].sort();
  tabContainer.innerHTML = "";
  ["All", ...groups].forEach(g => {
    const btn = document.createElement("button");
    btn.className = "tab" + (g === currentGroup ? " active" : "");
    btn.textContent = g;
    const color = GROUP_COLORS[g] || GROUP_COLORS["Other"];
    if (g !== "All") btn.style.setProperty("--tab-color", color);
    btn.addEventListener("click", () => {
      currentGroup = g;
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      btn.classList.add("active");
      renderPersonas();
    });
    tabContainer.appendChild(btn);
  });
}

// ----- Render -----
function renderPersonas() {
  const filtered = currentGroup === "All"
    ? allPersonas
    : allPersonas.filter(p => p.group === currentGroup);

  if (filtered.length === 0) {
    mainEl.innerHTML = "";
    summaryEl.textContent = "";
    renderState("empty", "No personas found for the selected filter.");
    return;
  }

  // Sort: by group then tribe_label
  filtered.sort((a, b) =>
    (a.group || "").localeCompare(b.group || "") ||
    (a.tribe_label || "").localeCompare(b.tribe_label || "")
  );

  const laName = laSelect.options[laSelect.selectedIndex]?.text ?? currentLa;
  summaryEl.innerHTML = `Showing <strong>${filtered.length}</strong> persona${filtered.length !== 1 ? "s" : ""} for <strong>${laName}</strong>`;

  const grid = document.createElement("div");
  grid.className = "persona-grid";

  let lastGroup = null;
  filtered.forEach(persona => {
    // Group section header
    if (persona.group !== lastGroup) {
      lastGroup = persona.group;
      if (currentGroup === "All") {
        const header = buildGroupHeader(persona.group, filtered.filter(p => p.group === persona.group).length);
        grid.appendChild(header);
      }
    }
    grid.appendChild(buildCard(persona));
  });

  mainEl.innerHTML = "";
  mainEl.appendChild(grid);
}

function buildGroupHeader(group, count) {
  const el = document.createElement("div");
  el.className = "group-header";
  const color = GROUP_COLORS[group] || GROUP_COLORS["Other"];
  el.innerHTML = `
    <span class="group-dot" style="background:${color}"></span>
    <h2>${group}</h2>
    <span class="group-count">${count} persona${count !== 1 ? "s" : ""}</span>
  `;
  return el;
}

function buildCard(persona) {
  const color = GROUP_COLORS[persona.group] || GROUP_COLORS["Other"];

  const card = document.createElement("div");
  card.className = "card";
  card.style.setProperty("--card-color", color);

  const totalPop = formatNum(persona.size);

  // Stats rows
  const statsHtml = STATS.map(({ key, label, unit, fmt, round }) => {
    const raw = persona[key];
    let val = "—";
    const num = Number(raw);
    if (raw !== null && raw !== undefined && raw !== "" && !(num < 0)) {
      if (fmt === "currency") val = "£" + formatNum(Math.round(num));
      else if (fmt === "number") val = formatNum(Math.round(num));
      else if (round !== undefined) val = num.toFixed(round) + (unit || "");
      else val = String(raw) + (unit || "");
    }
    return `<div class="stat-item"><span class="stat-label">${label}</span><span class="stat-value">${val}</span></div>`;
  }).join("");

  // Employment status text
  const empStatus = persona["Employment status"] || "—";

  // Religion
  const religion = persona["Religion"];
  const religionHtml = (religion && religion !== "None/Not applicable")
    ? `<div class="emp-breakdown"><strong>Religion:</strong> ${religion}</div>`
    : "";

  // Flag chips
  const flagsHtml = FLAG_COLS.map(col => {
    const v = persona[col];
    const isYes = v === "Yes" || v === true || v === 1;
    return `<span class="flag ${isYes ? "yes" : "no"}">${col}</span>`;
  }).join("");

  card.innerHTML = `
    <div class="card-head">
      <span class="card-title">${persona.tribe_label ?? "Persona"}</span>
      <span class="card-size">${totalPop} people</span>
    </div>
    <span class="card-group-badge" style="--card-color:${color}">${persona.group}</span>
    <div class="card-stats">
      <div class="stats-grid">${statsHtml}</div>
      <div class="emp-breakdown">
        <strong>Employment mix:</strong> ${empStatus}
      </div>
      ${religionHtml}
      <div class="flag-row">${flagsHtml}</div>
    </div>
  `;
  return card;
}

// ----- State helpers -----
function renderState(type, message) {
  const icons = { loading: "⏳", empty: "🗺️", error: "⚠️" };
  summaryEl.textContent = "";
  mainEl.innerHTML = `
    <div class="state-msg">
      <div class="icon">${icons[type] ?? ""}</div>
      <p>${message}</p>
    </div>
  `;
}

// ----- Utils -----
async function apiFetch(path) {
  const res = await fetch(API_BASE + path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function formatNum(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  return Number(n).toLocaleString("en-GB");
}

// ----- Start -----
init();
