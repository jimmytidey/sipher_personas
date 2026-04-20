/* =========================================================
   Archetypes – App Logic
   ========================================================= */

const API_BASE = window.location.port === "3000" ? "http://localhost:8000" : "";

// ----- State -----
const currentLevel     = "local";
let currentClusterType = "values";  // 'values' | 'llm_gemini' | 'llm_claude'
let currentLadcd       = null;
let allClusters        = [];

// ----- DOM refs -----
const clusterTypeSelect = document.getElementById("cluster-type");
const laSelect          = document.getElementById("la-select");
const mainEl            = document.getElementById("main-content");
const summaryEl         = document.getElementById("summary-bar");

// ----- Palette -----
const CLUSTER_PALETTE = [
  "#4f46e5", "#0891b2", "#059669", "#d97706", "#dc2626",
  "#7c3aed", "#db2777", "#ea580c", "#65a30d", "#0284c7",
];
function clusterColor(id) {
  return CLUSTER_PALETTE[(id - 1) % CLUSTER_PALETTE.length];
}

// ----- Boot -----
async function init() {
  renderState("loading", "Loading…");
  _readUrlState();
  await _applyState();
}

// ----- URL state sync -----
function _readUrlState() {
  const params = new URLSearchParams(window.location.hash.slice(1));
  const type   = params.get("type");
  const la     = params.get("la");
  if (type) currentClusterType = type;
  if (la)   currentLadcd = la;
  clusterTypeSelect.value = currentClusterType;
}

function _writeUrlState() {
  const params = new URLSearchParams();
  params.set("type", currentClusterType);
  if (currentLadcd) params.set("la", currentLadcd);
  const hash = "#" + params.toString();
  if (window.location.hash !== hash) {
    history.pushState(null, "", hash);
  }
}

window.addEventListener("popstate", async () => {
  _readUrlState();
  _syncLevelUi();
  await _applyState();
});

// Apply current state vars to the UI and fetch — shared by init + popstate
async function _applyState() {
  await populateLaDropdown(currentLadcd);
}

// ----- Employment status grouping -----
// Canonical display order for employment groups (jbstat labels from pipeline)
const _EMP_ORDER = [
  "Employed", "Self-employed", "Unemployed", "Retired",
  "Student", "Maternity", "Family care", "LT sick/disabled", "Other",
];

// Colours keyed by group position in _EMP_ORDER
const _EMP_PALETTE = [
  "#0891b2", // Employed      — teal
  "#7c3aed", // Self-employed — violet
  "#dc2626", // Unemployed    — red
  "#f59e0b", // Retired       — amber
  "#10b981", // Student       — green
  "#db2777", // Maternity     — pink
  "#ea580c", // Family care   — orange
  "#6b7280", // LT sick       — grey
  "#4f46e5", // Other         — indigo
];

function _empGroup(cluster) {
  // Prefer the explicit group column (set by HIERARCHICAL_CLUSTER in notebooks 14/15);
  // fall back to the modal jbstat value that cluster_summary.py always writes.
  const g = cluster.group;
  if (g != null && String(g).trim() !== "" && String(g).trim() !== "None" && isNaN(Number(g))) return String(g).trim();
  const j = cluster.jbstat;
  if (j != null && String(j).trim() !== "") return String(j).trim();
  return null;
}

function _sortedGroups(clusters) {
  const found = [...new Set(clusters.map(_empGroup).filter(Boolean))];
  // Sort by canonical order; unknowns go to the end
  return found.sort((a, b) => {
    const ai = _EMP_ORDER.indexOf(a);
    const bi = _EMP_ORDER.indexOf(b);
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });
}

function _groupColor(groupName) {
  const i = _EMP_ORDER.indexOf(groupName);
  return i >= 0 ? _EMP_PALETTE[i] : "#4f46e5";
}

// ----- Type / LA change handlers -----
clusterTypeSelect.addEventListener("change", async () => {
  currentClusterType = clusterTypeSelect.value;
  await populateLaDropdown(currentLadcd);   // keep LA selection when switching type
});

laSelect.addEventListener("change", () => {
  currentLadcd = laSelect.value || null;
  loadClusters();
});

// ----- Populate LA dropdown -----
async function populateLaDropdown(desiredLadcd = null) {
  laSelect.innerHTML = '<option value="">— loading —</option>';
  renderState("loading", "Loading Local Authorities…");
  try {
    const las = await apiFetch(`/local-las?cluster_type=${currentClusterType}`);
    laSelect.innerHTML = las.length
      ? las.map(la => `<option value="${la.code}">${la.name}</option>`).join("")
      : '<option value="">No LAs available</option>';
    const match = desiredLadcd && las.find(la => la.code === desiredLadcd);
    currentLadcd = match ? match.code : (las.length ? las[0].code : null);
    if (currentLadcd) laSelect.value = currentLadcd;
    await loadClusters();
  } catch (e) {
    laSelect.innerHTML = '<option value="">Error loading LAs</option>';
    renderState("error", `Could not load LAs: ${e.message}`);
  }
}

// ----- Load clusters -----
async function loadClusters() {
  renderState("loading", "Loading clusters…");
  try {
    if (!currentLadcd) { renderState("empty", "Select a Local Authority."); return; }
    allClusters = await apiFetch(`/local-clusters?ladcd=${currentLadcd}&cluster_type=${currentClusterType}`);
    _writeUrlState();
    renderClusters();
  } catch (e) {
    renderState("error", `Could not load clusters: ${e.message}<br><small>Is the API running? <code>uvicorn api.main:app --reload</code></small>`);
  }
}

// ----- Render -----
function renderClusters() {
  if (!allClusters.length) {
    renderState("empty", "No clusters found. Run the pipeline first.");
    return;
  }

  const methodLabel = { values: "Old school statistical clustering", llm_gemini: "LLM Gemini", llm_claude: "LLM Claude" }[currentClusterType] ?? currentClusterType;
  const groups = _sortedGroups(allClusters);
  const isGrouped = groups.length > 0;

  const ladnm = allClusters[0]?.ladnm ?? currentLadcd;
  const totalPop = allClusters.reduce((s, c) => s + (Number(c.size) || 0), 0);
  if (isGrouped) {
    summaryEl.innerHTML =
      `<strong>${allClusters.length}</strong> ${methodLabel} clusters across ` +
      `<strong>${groups.length}</strong> employment groups · ` +
      `<strong>${ladnm}</strong> · synthetic population <strong>${formatNum(totalPop)}</strong>`;
  } else {
    summaryEl.innerHTML =
      `<strong>${allClusters.length}</strong> ${methodLabel} clusters · ` +
      `<strong>${ladnm}</strong> · synthetic population <strong>${formatNum(totalPop)}</strong>`;
  }

  mainEl.innerHTML = "";
  const grid = document.createElement("div");
  grid.className = "persona-grid";

  if (isGrouped) {
    groups.forEach(group => {
      const groupClusters = allClusters.filter(c => _empGroup(c) === group);
      const groupPop = groupClusters.reduce((s, c) => s + (Number(c.size) || 0), 0);
      const color = _groupColor(group);

      const header = document.createElement("div");
      header.className = "group-header";
      header.innerHTML = `
        <span class="group-dot" style="background:${color}"></span>
        <h2>${group}</h2>
        <span class="group-count">${groupClusters.length} cluster${groupClusters.length !== 1 ? "s" : ""} · ${formatNum(Math.round(groupPop))} people</span>
      `;
      grid.appendChild(header);

      groupClusters.forEach((cluster, idx) =>
        grid.appendChild(buildCard(cluster, { groupColor: color, groupIndex: idx + 1 }))
      );
    });
  } else {
    allClusters.forEach(cluster => grid.appendChild(buildCard(cluster)));
  }

  mainEl.appendChild(grid);
}

function buildCard(cluster, { groupColor = null, groupIndex = null } = {}) {
  const color = groupColor ?? clusterColor(cluster.cluster_id);
  const badgeLabel = groupColor && groupIndex != null
    ? `${_empGroup(cluster) ?? "Group"} · ${groupIndex}`
    : `Cluster ${cluster.cluster_id}`;
  const card  = document.createElement("div");
  card.className = "card";
  card.style.setProperty("--card-color", color);

  const popSize  = Number(cluster.size);
  const pctLabel = cluster.pct_of_la != null
    ? `${cluster.pct_of_la}% of LA`
    : cluster.size != null
      ? (() => {
          const totalPop = allClusters.reduce((s, c) => s + (Number(c.size) || 0), 0);
          return totalPop > 0 && !isNaN(popSize)
            ? `${((popSize / totalPop) * 100).toFixed(1)}% of LA`
            : null;
        })()
      : null;

  const sizeLabel = !isNaN(popSize)
    ? (pctLabel ? `${formatNum(Math.round(popSize))} people · ${pctLabel}` : `${formatNum(Math.round(popSize))} people`)
    : "—";

  const respN     = cluster.n_respondents;
  const respLabel = respN != null ? `${formatNum(respN)} survey respondents` : "";

  // National clusters have full demographic stats; local clusters have size only for now
  const HEALTH_LABELS = { 1: "Excellent", 2: "Very good", 3: "Good", 4: "Fair", 5: "Poor" };

  const STAT_DEFS = [
    { key: "age",          label: "Age (mean)",                    unit: " yrs", round: 1 },
    { key: "racel_dv",     label: "Ethnicity (modal)",             pctKey: "racel_dv_pct" },
    { key: "hiqual_dv",    label: "Qualification (modal)",         pctKey: "hiqual_dv_pct" },
    { key: "marstat_dv",   label: "Marital status",                pctKey: "marstat_dv_pct" },
    { key: "tenure_dv",    label: "Housing tenure",                pctKey: "tenure_dv_pct" },
    { key: "hhtype_dv",    label: "Household type",                pctKey: "hhtype_dv_pct" },
    { key: "health",       label: "Self-reported health (mean)",   round: 1, labelMap: HEALTH_LABELS },
  ];

  const statsHtml = STAT_DEFS.map(({ key, label, unit, round, pctKey, labelMap }) => {
    const raw = cluster[key];
    if (raw == null || raw === "") return "";
    let val;
    if (pctKey) {
      const pct = cluster[pctKey];
      val = pct != null ? `${raw} (${pct}%)` : String(raw);
    } else if (round !== undefined) {
      const num = Number(raw);
      if (isNaN(num)) {
        val = String(raw);
      } else if (labelMap) {
        const text = labelMap[Math.round(num)] ?? "";
        val = text ? `${text} (${num.toFixed(round)})` : num.toFixed(round);
      } else {
        val = num.toFixed(round) + (unit || "");
      }
    } else {
      val = String(raw) + (unit || "");
    }
    return `<div class="stat-item"><span class="stat-label">${label}</span><span class="stat-value">${val}</span></div>`;
  }).join("");

  const locationBadge = cluster.ladnm
    ? `<div class="card-location">${cluster.ladnm}</div>`
    : "";

  const descHtml = cluster.tribe_description
    ? `<div class="card-description">${cluster.tribe_description}</div>`
    : "";

  const reasoningText = (cluster.reasoning ?? "").trim();
  const reasoningHtml = reasoningText ? `
    <button class="card-expand-btn" aria-expanded="false">
      <span>LLM reasoning</span>
      <svg class="expand-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 6 8 10 12 6"/></svg>
    </button>
    <div class="card-extra card-reasoning" hidden>
      <p class="reasoning-text">${reasoningText}</p>
    </div>` : "";

  card.innerHTML = `
    <div class="card-head">
      <div class="cluster-badge" style="background:${color}">${badgeLabel}</div>
      <div class="card-head-text">
        <div class="card-title">${cluster.tribe_label}</div>
        <span class="card-size">${sizeLabel}</span>
      </div>
    </div>
    ${locationBadge}
    ${descHtml}
    ${respLabel ? `<div class="card-resp-note">${respLabel}</div>` : ""}
    ${statsHtml ? `<div class="card-stats"><div class="stats-grid">${statsHtml}</div></div>` : ""}
    ${reasoningHtml}
  `;

  const expandBtn = card.querySelector(".card-expand-btn");
  if (expandBtn) {
    expandBtn.addEventListener("click", () => {
      const expanded = expandBtn.getAttribute("aria-expanded") === "true";
      expandBtn.setAttribute("aria-expanded", String(!expanded));
      card.querySelector(".card-reasoning").hidden = expanded;
    });
  }

  return card;
}

// ----- State helpers -----
function renderState(type, message) {
  const icons = { loading: "⏳", empty: "🗺️", error: "⚠️" };
  summaryEl.textContent = "";
  mainEl.innerHTML = `
    <div class="state-msg">
      <div class="icon">${icons[type] ?? ""}</div>
      ${message ? `<p>${message}</p>` : ""}
    </div>
  `;
}

// ----- Utils -----
async function apiFetch(path) {
  const res = await fetch(API_BASE + path);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail !== undefined) {
        const d = body.detail;
        msg += `: ${typeof d === "string" ? d : JSON.stringify(d)}`;
      }
    } catch { /* ignore */ }
    throw new Error(msg);
  }
  return res.json();
}

function formatNum(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  return Number(n).toLocaleString("en-GB");
}

// ----- Start -----
init();

