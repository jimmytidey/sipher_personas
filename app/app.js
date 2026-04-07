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

/** Escape HTML, then render **bold** and newlines for gpt_description (markdown-lite). */
function formatGptDescriptionHtml(raw) {
  if (!raw) return "";
  const esc = (s) =>
    s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  let t = esc(String(raw));
  t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/\n/g, "<br>");
  return t;
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

// Hard-coded current variables from config_variables_sipher_weighted.py
// Keys must match cluster CSV headers (VARIABLE_MAP labels). `code` is what we display.
const STATS = [
  { key: "Age", code: "doby_dv", round: 1, unit: " yrs" },
  { key: "Sex (Derived)", code: "sex_dv", pctKey: "Sex (Derived) %" },
  { key: "Ethnic group", code: "racel_dv", pctKey: "Ethnic group %" },
  { key: "Highest qualification", code: "hiqual_dv", pctKey: "Highest qualification %" },
  { key: "Employment status", code: "jbstat" },
  { key: "Marital status", code: "marstat_dv", pctKey: "Marital status %" },
  { key: "Housing tenure (Own/Rent)", code: "tenure_dv", pctKey: "Housing tenure (Own/Rent) %" },
  { key: "Composition of household (LFS)", code: "hhtype_dv", pctKey: "Composition of household (LFS) %" },
  { key: "Self-rated general health", code: "scsf1", pctKey: "Self-rated general health %" },
];

// Disabled for now; we only show the current config vars above.
const EXTRA_VARS = [];

// ----- State -----
let currentLa    = null;
let currentGroup = "All";
let currentMode  = "local";    // "local" | "national"
let allPersonas  = [];

// ----- DOM refs -----
const laSelect     = document.getElementById("la-select");
const tabContainer = document.getElementById("group-tabs");
const mainEl       = document.getElementById("main-content");
const summaryEl    = document.getElementById("summary-bar");
const siteIntro    = document.getElementById("site-intro");
const modeToggle   = document.getElementById("mode-toggle");

function setSiteIntroVisible(show) {
  if (siteIntro) siteIntro.hidden = !show;
}

function modeApiPath(path) {
  const sep = path.includes("?") ? "&" : "?";
  return path + sep + `mode=${currentMode}`;
}

function fullApiPath(path) {
  return modeApiPath(apiPath(path));
}

// ----- Mode toggle -----
if (modeToggle) {
  modeToggle.addEventListener("click", async (e) => {
    const btn = e.target.closest(".mode-btn");
    if (!btn || btn.dataset.mode === currentMode) return;

    currentMode = btn.dataset.mode;
    modeToggle.querySelectorAll(".mode-btn").forEach(b =>
      b.classList.toggle("active", b.dataset.mode === currentMode)
    );

    // Reload LA list for new mode (available LAs may differ)
    currentLa    = null;
    currentGroup = "All";
    allPersonas  = [];
    laSelect.value = "";
    tabContainer.innerHTML = "";
    mainEl.innerHTML = "";
    summaryEl.textContent = "";
    setSiteIntroVisible(false);

    renderState("loading", "Loading local authorities…");
    try {
      const las = await apiFetch(fullApiPath("/las"));
      populateLaSelect(las);
    } catch (e) {
      renderState("error", `Could not load LAs for ${currentMode} mode: ${e.message}`);
    }
  });
}

// ----- Boot -----
async function init() {
  // Show test-mode banner if ?test=true
  if (IS_TEST) {
    const banner = document.createElement("div");
    banner.id = "test-banner";
    banner.textContent = "⚠️ TEST MODE — showing data_test/ output";
    document.body.prepend(banner);
  }

  renderState("loading", "Loading local authorities…");
  try {
    const las = await apiFetch(fullApiPath("/las"));
    populateLaSelect(las);
  } catch (e) {
    renderState("error", `Could not reach API at ${API_BASE}. Is it running?<br><code>uvicorn api.main:app --reload</code>`);
  }
}

function populateLaSelect(las) {
  const label = document.querySelector('label[for="la-select"]');
  if (label) {
    label.textContent =
      las.length > 0
        ? `Local authority (${las.length} in this dataset)`
        : "Local authority";
  }
  laSelect.innerHTML = '<option value="">— Select a local authority —</option>';
  las.forEach(({ code, name }) => {
    const opt = document.createElement("option");
    opt.value = code;
    opt.textContent = `${name} (${code})`;
    laSelect.appendChild(opt);
  });
  laSelect.disabled = false;
  setSiteIntroVisible(true);
  renderState("empty", "");
}

laSelect.addEventListener("change", async () => {
  const code = laSelect.value;
  if (!code) {
    setSiteIntroVisible(true);
    renderState("empty", "");
    return;
  }
  currentLa    = code;
  currentGroup = "All";
  setSiteIntroVisible(false);
  renderState("loading", "Loading personas…");
  try {
    allPersonas = await apiFetch(fullApiPath(`/la/${code}/personas`));
    buildGroupTabs();
    renderPersonas();
  } catch (e) {
    renderState("error", `Failed to load personas for ${code}: ${e.message}`);
  }
});

// ----- Group tabs -----
function buildGroupTabs() {
  const groups = [...new Set(allPersonas.map(p => p.group).filter(Boolean))].sort();
  const totalPop = allPersonas.reduce((s, p) => s + (Number(p.size) || 0), 0);
  tabContainer.innerHTML = "";
  ["All", ...groups].forEach(g => {
    const btn = document.createElement("button");
    btn.className = "tab" + (g === currentGroup ? " active" : "");
    if (g === "All") {
      btn.textContent = "All";
    } else {
      const groupPop = allPersonas.filter(p => p.group === g).reduce((s, p) => s + (Number(p.size) || 0), 0);
      const pct = totalPop > 0 ? Math.round(groupPop / totalPop * 100) : 0;
      btn.textContent = `${g} (${pct}%)`;
    }
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
  const modeLabel = currentMode === "national" ? " · national clusters" : " · local clusters";
  summaryEl.innerHTML = `Showing <strong>${filtered.length}</strong> persona${filtered.length !== 1 ? "s" : ""} for <strong>${laName}</strong><span class="mode-label">${modeLabel}</span>`;

  const totalPop = allPersonas.reduce((s, p) => s + (Number(p.size) || 0), 0);

  const grid = document.createElement("div");
  grid.className = "persona-grid";

  let lastGroup = null;
  filtered.forEach(persona => {
    // Group section header
    if (persona.group !== lastGroup) {
      lastGroup = persona.group;
      if (currentGroup === "All") {
        const groupPersonas = filtered.filter(p => p.group === persona.group);
        const groupPop = groupPersonas.reduce((s, p) => s + (Number(p.size) || 0), 0);
        const pct = totalPop > 0 ? Math.round(groupPop / totalPop * 100) : 0;
        const header = buildGroupHeader(persona.group, groupPersonas.length, pct);
        grid.appendChild(header);
      }
    }
    grid.appendChild(buildCard(persona, totalPop));
  });

  mainEl.innerHTML = "";
  mainEl.appendChild(grid);
}

function buildGroupHeader(group, count, pct) {
  const el = document.createElement("div");
  el.className = "group-header";
  const color = GROUP_COLORS[group] || GROUP_COLORS["Other"];
  el.innerHTML = `
    <span class="group-dot" style="background:${color}"></span>
    <h2>${group}</h2>
    <span class="group-count">${pct}% of population · ${count} persona${count !== 1 ? "s" : ""}</span>
  `;
  return el;
}

function buildCard(persona, totalPop) {
  const color = GROUP_COLORS[persona.group] || GROUP_COLORS["Other"];

  const card = document.createElement("div");
  card.className = "card";
  card.style.setProperty("--card-color", color);

  const clusterN = Number(persona.size);
  const countPart =
    persona.size != null && persona.size !== "" && !isNaN(clusterN) && clusterN >= 0
      ? `${formatNum(Math.round(clusterN))} people`
      : null;
  const pctPart =
    totalPop > 0 && !isNaN(clusterN) && clusterN >= 0
      ? `${((clusterN / totalPop) * 100).toFixed(1)}% of LA`
      : null;
  const pct =
    pctPart && countPart
      ? `${pctPart} (${countPart})`
      : pctPart
        ? pctPart
        : countPart
          ? countPart
          : "—";

  // GPT-generated title & description (may be absent before notebook 9 is run)
  const gptTitle = persona.gpt_title;
  const titleBlockHtml = gptTitle
    ? `<div class="card-gpt-title">${gptTitle}</div><div class="card-subtitle">${persona.tribe_label ?? ""}</div>`
    : `<div class="card-title">${persona.tribe_label ?? "Persona"}</div>`;

  // Stats rows
  const statsHtml = STATS.map(({ key, code, label, unit, fmt, round, lookup, pctKey }) => {
    const raw = persona[key];
    let val = "—";
    if (pctKey !== undefined) {
      const pRaw = persona[pctKey];
      if (raw !== null && raw !== undefined && raw !== "") {
        const pNum = Number(pRaw);
        const pctStr =
          pRaw !== null && pRaw !== undefined && pRaw !== "" && !Number.isNaN(pNum)
            ? ` (${pNum}%)`
            : "";
        val = `${raw}${pctStr}`;
      }
    } else {
      const num = Number(raw);
      if (raw !== null && raw !== undefined && raw !== "" && !(num < 0)) {
        if (lookup) val = lookup[Math.round(num)] ?? String(Math.round(num));
        else if (fmt === "currency") val = "£" + formatNum(Math.round(num));
        else if (fmt === "number") val = formatNum(Math.round(num));
        else if (round !== undefined) val = num.toFixed(round) + (unit || "");
        else val = String(raw) + (unit || "");
      }
    }
    const statLabel = code ?? label ?? key;
    return `<div class="stat-item"><span class="stat-label">${statLabel}</span><span class="stat-value">${val}</span></div>`;
  }).join("");

  const portraitHtml = persona.portrait_url
    ? `<img class="card-portrait" src="${API_BASE}${persona.portrait_url}" alt="${persona.gpt_title || persona.tribe_label}" />`
    : "";

  const descriptionHtml = persona.gpt_description
    ? `<div class="card-description">${formatGptDescriptionHtml(persona.gpt_description)}</div>`
    : "";

  // Extra variables for the expanded section (always show a row; — if not in API payload yet)
  const extraHtml = EXTRA_VARS.map(({ key, code, label, unit, fmt, round, lookup }) => {
    const raw = persona[key];
    const statLabel = code ?? label ?? key;
    if (raw === null || raw === undefined || raw === "") {
      return `<div class="stat-item"><span class="stat-label">${statLabel}</span><span class="stat-value">—</span></div>`;
    }
    const num = Number(raw);
    let val;
    if (lookup && !isNaN(num)) val = lookup[Math.round(num)] ?? String(Math.round(num));
    else if (fmt === "currency" && !isNaN(num)) val = "£" + formatNum(Math.round(num));
    else if (round !== undefined && !isNaN(num)) val = num.toFixed(round) + (unit || "");
    else val = String(raw) + (unit || "");
    return `<div class="stat-item"><span class="stat-label">${statLabel}</span><span class="stat-value">${val}</span></div>`;
  }).join("");

  const showExtra = EXTRA_VARS.length > 0;
  card.innerHTML = `
    <div class="card-head">
      ${portraitHtml}
      <div class="card-head-text">
        <div class="card-title-block">${titleBlockHtml}</div>
        <span class="card-size">${pct}</span>
      </div>
    </div>
    <div class="card-stats">
      <div class="stats-grid">${statsHtml}</div>
      ${descriptionHtml}
    </div>
    ${showExtra ? `<button class="card-expand-btn" aria-expanded="false">
      <span>Show all variables</span>
      <svg class="expand-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 6 8 10 12 6"/></svg>
    </button>` : ""}
    ${showExtra ? `<div class="card-extra" hidden>
      <div class="stats-grid extra-grid">${extraHtml}</div>
    </div>` : ""}
  `;

  const expandBtn = card.querySelector(".card-expand-btn");
  if (expandBtn) {
    expandBtn.addEventListener("click", function () {
      const extra    = card.querySelector(".card-extra");
      const expanded = this.getAttribute("aria-expanded") === "true";
      if (extra) extra.hidden = expanded;
      this.setAttribute("aria-expanded", String(!expanded));
      this.querySelector("span").textContent = expanded ? "Show all variables" : "Hide variables";
    });
  }

  return card;
}

// ----- State helpers -----
function renderState(type, message) {
  const icons = { loading: "⏳", empty: "🗺️", error: "⚠️" };
  summaryEl.textContent = "";
  const textHtml = message ? `<p>${message}</p>` : "";
  mainEl.innerHTML = `
    <div class="state-msg">
      <div class="icon">${icons[type] ?? ""}</div>
      ${textHtml}
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
