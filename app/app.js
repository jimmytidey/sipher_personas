/* =========================================================
   Archetypes – App Logic
   ========================================================= */

// In dev the frontend runs on :3000 and the API on :8000.
// In production (Azure / single-process) both are on the same origin.
const API_BASE = window.location.port === "3000" ? "http://localhost:8000" : "";

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

// Numeric stats to show on cards — cluster variables only
const NSSEC_LABELS = {
  0: "Unknown",
  1: "Large employers & higher management",
  2: "Higher professional",
  3: "Lower management & professional",
  4: "Intermediate",
  5: "Small employers & own account",
  6: "Lower supervisory & technical",
  7: "Semi-routine",
  8: "Routine",
};

const HIQUAL_LABELS = {
  1: "Degree",
  2: "Other Higher",
  3: "A-Level",
  4: "GCSE",
  5: "Other / None",
};

const STATS = [
  { key: "Derived age at interview",              label: "Avg. age",          unit: " yrs",  round: 1 },
  { key: "Total monthly personal income (gross)", label: "Monthly income",    unit: "",      fmt: "currency" },
  { key: "Social class (NS-SEC 8)",               label: "Employment type",  unit: "",      lookup: NSSEC_LABELS },
  { key: "Number of own children in household",   label: "Children",          unit: "",      round: 0 },
  { key: "Highest qualification",                 label: "Qual. level",      unit: "",      lookup: HIQUAL_LABELS },
];

// Extra variables revealed when a card is expanded
const EXTRA_VARS = [
  { key: "Gender",                                        label: "Gender" },
  { key: "Household size",                                label: "Household size",           round: 1 },
  { key: "Has children",                                  label: "Has children" },
  { key: "Monthly net pay (take-home)",                   label: "Monthly net pay",          fmt: "currency" },
  { key: "Mental health score (SF-12 MCS)",               label: "Mental health score",      round: 1 },
  { key: "Physical health score (SF-12 PCS)",             label: "Physical health score",    round: 1 },
  { key: "Buckner Neighbourhood Cohesion Index",          label: "Neighbourhood cohesion",   round: 1 },
  { key: "Standard of local services: Public transport",  label: "Local svcs: Transport",    round: 1 },
  { key: "Standard of local services: Shopping",          label: "Local svcs: Shopping",     round: 1 },
  { key: "Standard of local services: Leisure",           label: "Local svcs: Leisure",      round: 1 },
  { key: "Minutes spent travelling to work",              label: "Commute (mins)",           round: 0 },
  { key: "Environmental habit: public transport use",     label: "PT use habit" },
  { key: "Miles driven in last 12 months",                label: "Miles driven/yr",          round: 0 },
  { key: "Has use of a car or van",                       label: "Has car/van" },
  { key: "Work location",                                 label: "Work location" },
  { key: "Main mode of transport to work",               label: "Transport to work" },
  { key: "Employment status",                             label: "Employment status" },
  { key: "Internet use frequency",                        label: "Internet use" },
];

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

  const totalPop = allPersonas.reduce((s, p) => s + (Number(p.size) || 0), 0);

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
    grid.appendChild(buildCard(persona, totalPop));
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

function buildCard(persona, totalPop) {
  const color = GROUP_COLORS[persona.group] || GROUP_COLORS["Other"];

  const card = document.createElement("div");
  card.className = "card";
  card.style.setProperty("--card-color", color);

  const pct = totalPop > 0 ? ((Number(persona.size) / totalPop) * 100).toFixed(1) + "% of LA" : "—";

  // GPT-generated title & description (may be absent before notebook 9 is run)
  const gptTitle = persona.gpt_title;
  const titleBlockHtml = gptTitle
    ? `<div class="card-gpt-title">${gptTitle}</div><div class="card-subtitle">${persona.tribe_label ?? ""}</div>`
    : `<div class="card-title">${persona.tribe_label ?? "Persona"}</div>`;

  // Stats rows
  const statsHtml = STATS.map(({ key, label, unit, fmt, round, lookup }) => {
    const raw = persona[key];
    let val = "—";
    const num = Number(raw);
    if (raw !== null && raw !== undefined && raw !== "" && !(num < 0)) {
      if (lookup)           val = lookup[Math.round(num)] ?? String(Math.round(num));
      else if (fmt === "currency") val = "£" + formatNum(Math.round(num));
      else if (fmt === "number")   val = formatNum(Math.round(num));
      else if (round !== undefined) val = num.toFixed(round) + (unit || "");
      else val = String(raw) + (unit || "");
    }
    return `<div class="stat-item"><span class="stat-label">${label}</span><span class="stat-value">${val}</span></div>`;
  }).join("");

  // Categorical cluster variables
  const religion = persona["Religion"];
  const religionHtml = religion
    ? `<div class="emp-breakdown"><strong>Religion:</strong> ${religion}</div>`
    : "";

  const ethnicity = persona["Ethnic group"];
  const ethnicityHtml = ethnicity
    ? `<div class="emp-breakdown"><strong>Ethnic group:</strong> ${ethnicity}</div>`
    : "";

  const englangRaw = persona["English is not first language"];
  const englangVal = englangRaw === "Yes" ? "No" : englangRaw === "No" ? "Yes" : "Yes";
  const englangHtml = `<div class="emp-breakdown"><strong>English is first language:</strong> ${englangVal}</div>`;

  const descriptionHtml = persona.gpt_description
    ? `<div class="card-description">${persona.gpt_description}</div>`
    : "";

  // Extra variables for the expanded section
  const extraHtml = EXTRA_VARS.map(({ key, label, unit, fmt, round }) => {
    const raw = persona[key];
    if (raw === null || raw === undefined || raw === "") return "";
    const num = Number(raw);
    let val;
    if (fmt === "currency" && !isNaN(num)) val = "£" + formatNum(Math.round(num));
    else if (round !== undefined && !isNaN(num)) val = num.toFixed(round) + (unit || "");
    else val = String(raw) + (unit || "");
    return `<div class="stat-item"><span class="stat-label">${label}</span><span class="stat-value">${val}</span></div>`;
  }).join("");

  card.innerHTML = `
    <div class="card-head">
      <div class="card-title-block">${titleBlockHtml}</div>
      <span class="card-size">${pct}</span>
    </div>
    <div class="card-stats">
      <div class="stats-grid">${statsHtml}</div>
      ${descriptionHtml}
      ${ethnicityHtml}
      ${religionHtml}
      ${englangHtml}
    </div>
    <button class="card-expand-btn" aria-expanded="false">
      <span>Show all variables</span>
      <svg class="expand-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 6 8 10 12 6"/></svg>
    </button>
    <div class="card-extra" hidden>
      <div class="stats-grid extra-grid">${extraHtml}</div>
    </div>
  `;

  card.querySelector(".card-expand-btn").addEventListener("click", function () {
    const extra    = card.querySelector(".card-extra");
    const expanded = this.getAttribute("aria-expanded") === "true";
    extra.hidden   = expanded;
    this.setAttribute("aria-expanded", String(!expanded));
    this.querySelector("span").textContent = expanded ? "Show all variables" : "Hide variables";
  });

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
