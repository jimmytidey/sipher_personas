/* =========================================================
   Archetypes – App Logic
   ========================================================= */

const API_BASE = window.location.port === "3000" ? "http://localhost:8000" : "";

// ----- State -----
const currentLevel     = "local";
let currentClusterType = "llm_claude";  // 'values' | 'llm_gemini' | 'llm_claude'
let currentLadcd       = null;
let allClusters        = [];
let groupTotals        = {}; // group_label → total_population for current LA

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
// Maps numeric jbstat_eng group codes (as strings) to display labels.
// Must match EMP_LABELS in data_pipeline/helpers/llm_prompts.py.
const _EMP_GROUP_LABELS = {
  "1": "Employed",
  "3": "Unemployed",
  "4": "Retired",
  "5": "On leave",
  "7": "Student / training",
  "8": "Inactive",
};

// Canonical display order for employment groups
const _EMP_ORDER = [
  "Employed", "Unemployed", "Retired", "On leave", "Student / training", "Inactive",
];

// Colours keyed by group position in _EMP_ORDER
const _EMP_PALETTE = [
  "#0891b2", // Employed          — teal
  "#dc2626", // Unemployed        — red
  "#f59e0b", // Retired           — amber
  "#db2777", // On leave          — pink
  "#10b981", // Student/training  — green
  "#6b7280", // Inactive          — grey
];

function _empGroup(cluster) {
  // Resolve numeric group column (e.g. "1.0", "5.0") to a display label.
  const g = cluster.group;
  if (g != null && String(g).trim() !== "" && String(g).trim() !== "None") {
    const key = String(Math.round(Number(g)));
    if (_EMP_GROUP_LABELS[key]) return _EMP_GROUP_LABELS[key];
  }
  // Fall back to raw jbstat value if group is absent / unrecognised
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
    [allClusters] = await Promise.all([
      apiFetch(`/local-clusters?ladcd=${currentLadcd}&cluster_type=${currentClusterType}`),
      apiFetch(`/la-group-totals?ladcd=${currentLadcd}`).then(rows => {
        groupTotals = Object.fromEntries(rows.map(r => [r.group_label, r.total_population]));
      }).catch(() => { groupTotals = {}; }),
    ]);
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

  const clusters = allClusters;

  const methodLabel = { embedding: "Vector embedding (k-means)", values: "Values (k-means)", llm_gemini: "LLM Gemini", llm_claude: "LLM Claude" }[currentClusterType] ?? currentClusterType;
  const groups = _sortedGroups(clusters);
  const isGrouped = groups.length > 0;

  const ladnm = clusters[0]?.ladnm ?? currentLadcd;
  const totalPop = allClusters.reduce((s, c) => s + (Number(c.size) || 0), 0);
  summaryEl.textContent = "";

  mainEl.innerHTML = "";
  const grid = document.createElement("div");
  grid.className = "persona-grid";

  if (isGrouped) {
    groups.forEach(group => {
      const groupClusters = clusters.filter(c => _empGroup(c) === group).sort((a, b) => (Number(b.size) || 0) - (Number(a.size) || 0));
      const groupPop = groupClusters.reduce((s, c) => s + (Number(c.size) || 0), 0);
      const groupTotal = groupTotals[group] || 0;
      const coveragePct = groupTotal > 0 ? ((groupPop / groupTotal) * 100).toFixed(1) : null;
      const coverageStr = coveragePct && groupTotal > 0
        ? ` · ${coveragePct}% of ${formatNum(groupTotal)} ${group.toLowerCase()} people in ${ladnm}`
        : "";
      // Attach clustered-group pop to each cluster for use in buildCard
      groupClusters.forEach(c => { c._groupPop = groupPop; c._groupLabel = group; });
      const color = _groupColor(group);

      const header = document.createElement("div");
      header.className = "group-header";
      const reasoningForGroup = (groupClusters[0]?.reasoning ?? "").trim();
      header.innerHTML = `
        <span class="group-dot" style="background:${color}"></span>
        <h2>${group}</h2>
        <span class="group-count">${groupClusters.length} cluster${groupClusters.length !== 1 ? "s" : ""} · ${formatNum(Math.round(groupPop))} people clustered${coverageStr}</span>
        ${reasoningForGroup ? `<button class="reasoning-link">LLM reasoning</button>` : ""}
      `;
      if (reasoningForGroup) {
        header.querySelector(".reasoning-link").addEventListener("click", () => {
          window.openReasoningModal(reasoningForGroup);
        });
      }
      grid.appendChild(header);

      groupClusters.forEach((cluster, idx) =>
        grid.appendChild(buildCard(cluster, { groupColor: color, groupIndex: idx + 1 }))
      );
    });
  } else {
    [...clusters].sort((a, b) => (Number(b.size) || 0) - (Number(a.size) || 0)).forEach(cluster => grid.appendChild(buildCard(cluster)));
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
  const groupPop = Number(cluster._groupPop) || 0;
  const groupLabel = cluster._groupLabel || null;
  const pctOfGroup = groupPop > 0 && !isNaN(popSize)
    ? `${((popSize / groupPop) * 100).toFixed(1)}% of clustered ${groupLabel ?? "group"}`
    : null;
  const pctOfLa = cluster.pct_of_la != null
    ? `${cluster.pct_of_la}% of LA`
    : cluster.size != null
      ? (() => {
          const totalPop = allClusters.reduce((s, c) => s + (Number(c.size) || 0), 0);
          return totalPop > 0 && !isNaN(popSize)
            ? `${((popSize / totalPop) * 100).toFixed(1)}% of LA`
            : null;
        })()
      : null;

  const sizeLabel = pctOfGroup ?? pctOfLa ?? (isNaN(popSize) ? "—" : `${formatNum(Math.round(popSize))} people`);
  const popCountLabel = isNaN(popSize) ? null : `${formatNum(Math.round(popSize))} synthetic population records`;

  // National clusters have full demographic stats; local clusters have size only for now
  const HEALTH_LABELS = { 1: "Excellent", 2: "Very good", 3: "Good", 4: "Fair", 5: "Poor" };

  const STAT_DEFS = [
    { key: "age",          label: "Age (mean)",                    unit: " yrs", round: 1 },
    { key: "sex_dv",       label: "Sex",                           pctKey: "sex_dv_pct",      key2: "sex_dv_2",      pct2Key: "sex_dv_2_pct" },
    { key: "jbstat",       label: "Employment status",             pctKey: "jbstat_pct",      key2: "jbstat_2",      pct2Key: "jbstat_2_pct" },
    { key: "racel_dv",     label: "Ethnicity (modal)",             pctKey: "racel_dv_pct",    key2: "racel_dv_2",    pct2Key: "racel_dv_2_pct" },
    { key: "hiqual_dv",    label: "Qualification (modal)",         pctKey: "hiqual_dv_pct",   key2: "hiqual_dv_2",   pct2Key: "hiqual_dv_2_pct" },
    { key: "marstat_dv",   label: "Marital status",                pctKey: "marstat_dv_pct",  key2: "marstat_dv_2",  pct2Key: "marstat_dv_2_pct" },
    { key: "tenure_dv",    label: "Housing tenure",                pctKey: "tenure_dv_pct",   key2: "tenure_dv_2",   pct2Key: "tenure_dv_2_pct" },
    { key: "hhtype_dv",    label: "Household type",                pctKey: "hhtype_dv_pct",   key2: "hhtype_dv_2",   pct2Key: "hhtype_dv_2_pct" },
    { key: "health",       label: "Self-reported health (mean)",   round: 1, labelMap: HEALTH_LABELS },
  ];

  const statsHtml = STAT_DEFS.map(({ key, label, unit, round, pctKey, key2, pct2Key, labelMap }) => {
    const raw = cluster[key];
    if (raw == null || raw === "") return "";
    let val;
    if (pctKey) {
      const pct = cluster[pctKey];
      val = pct != null ? `${displayLabel(raw)} (${pct}%)` : displayLabel(String(raw));
      // Append second value if modal < 50% and second value exists
      const raw2 = cluster[key2];
      const pct2 = cluster[pct2Key];
      if (Number(pct) < 50 && raw2 != null && raw2 !== "") {
        val += pct2 != null ? `; ${displayLabel(raw2)} (${pct2}%)` : `; ${displayLabel(raw2)}`;
      }
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

  card.innerHTML = `
    <div class="card-head">
      <div class="card-head-text">
        <div class="card-title">${cluster.tribe_label}</div>
        <span class="card-size">${sizeLabel}</span>
      </div>
    </div>
    ${locationBadge}
    ${descHtml}
    ${popCountLabel ? `<div class="card-resp-note">${popCountLabel}</div>` : ""}
    ${statsHtml ? `<div class="card-stats"><div class="stats-grid">${statsHtml}</div></div>` : ""}
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

// Shorten verbose category labels for display only
const _LABEL_ALIASES = {
  "White: British/English/Scottish/Welsh/N. Irish": "White: British",
};
function displayLabel(val) {
  return _LABEL_ALIASES[val] ?? val;
}

function formatNum(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  return Number(n).toLocaleString("en-GB");
}

// ----- Start -----
init();

