from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

_API_DIR  = Path(__file__).resolve().parent
_ROOT_DIR = _API_DIR.parent
# Use api/data/ when it exists (self-contained deployment), else fall back to project root
BASE_DIR = _API_DIR if (_API_DIR / "data").exists() else _ROOT_DIR

PORTRAIT_DIR = _API_DIR / "data" / "portraits"

# ── Cluster CSV paths ─────────────────────────────────────────────────────────
# local  — clusters defined per-LA  (7_cluster_local_level)
# national — clusters defined nationally, then profiled per-LA  (8_cluster_national_level)

PROD_LOCAL_CLUSTERS_PATH    = BASE_DIR / "data" / "clusters" / "LA_london_clusters.csv"
PROD_NATIONAL_CLUSTERS_PATH = BASE_DIR / "data" / "clusters" / "LA_london_national_clusters.csv"

TEST_LOCAL_CLUSTERS_PATH    = BASE_DIR / "data_test" / "7_cluster_local_level" / "LA_clusters.csv"
TEST_NATIONAL_CLUSTERS_PATH = BASE_DIR / "data_test" / "8_cluster_national_level" / "LA_national_clusters.csv"

# Back-compat alias used in older call sites
PROD_CLUSTERS_PATH = PROD_LOCAL_CLUSTERS_PATH
TEST_CLUSTERS_PATH = TEST_LOCAL_CLUSTERS_PATH

app = FastAPI(title="Archetypes API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Data loaders — uncached so the CSV is read fresh on every request
# ---------------------------------------------------------------------------

def load_clusters(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Clusters file not found: {path}")
    return pd.read_csv(path)


def _normalize_unit_id(val: Any) -> str:
    """Stable string LA code from CSV or URL (handles int/float/str)."""
    if val is None:
        return ""
    if isinstance(val, float) and pd.isna(val):
        return ""
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if float(val).is_integer():
            return str(int(val))
        return str(val).strip()
    return str(val).strip()


def _rows_for_la(df: pd.DataFrame, ladcd: str) -> pd.DataFrame:
    """Rows for one LA — compares normalized unit_id so CSV/URL types always match."""
    want = _normalize_unit_id(ladcd)
    u = df["unit_id"].map(_normalize_unit_id)
    return df[u == want]


def _pick_cluster_csv(base: Path) -> Path:
    """
    Prefer *_described.csv only when it exists and is not older than the base export.

    After re-running step 6, LA_london_clusters.csv is refreshed but an old
    LA_london_clusters_described.csv may still sit beside it — loading described
    would show a stale LA list (e.g. 33 boroughs) until step 8 is re-run.
    """
    described = base.parent / (f"{base.stem}_described.csv")
    if not described.exists():
        return base
    if not base.exists():
        return described
    if described.stat().st_mtime >= base.stat().st_mtime:
        return described
    return base


def _clusters_path(test: bool, mode: str = "local") -> Path:
    if mode == "national":
        base = TEST_NATIONAL_CLUSTERS_PATH if test else PROD_NATIONAL_CLUSTERS_PATH
    else:
        base = TEST_LOCAL_CLUSTERS_PATH if test else PROD_LOCAL_CLUSTERS_PATH
    return _pick_cluster_csv(base)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/variable-defs")
def variable_defs() -> list[dict[str, str]]:
    """
    Ordered variable definitions from current config_variables.py.

    Returns [{"code": <base_code>, "label": <VARIABLE_MAP label>}, ...]
    in the same order as VARIABLES.
    """
    try:
        import data_pipeline.config_variables as cv
        cv.reload_config_variables()
        variables = cv.VARIABLES
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not load variable definitions: {exc}") from exc

    return [
        {"code": code, "label": str(v.get("label", code))}
        for code, v in variables.items()
    ]


@app.get("/las")
def list_las(
    test: bool = Query(default=False, description="Serve from data_test/ when true"),
    mode: str  = Query(default="local", description="Clustering mode: 'local' or 'national'"),
) -> list[dict[str, str]]:
    """Return one entry per distinct unit_id in the cluster CSV (no separate LA master list)."""
    try:
        df = load_clusters(_clusters_path(test, mode))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if "unit_id" not in df.columns:
        raise HTTPException(status_code=500, detail="Clusters CSV has no unit_id column")

    codes = df["unit_id"].map(_normalize_unit_id)
    mask = codes.str.len() > 0
    df = df.loc[mask].copy()
    df["_uid"] = codes[mask]

    if df.empty:
        return []

    if "la_name" in df.columns:
        # One row per LA: first non-empty name wins
        def _first_name(s: pd.Series) -> str:
            for v in s.dropna():
                t = str(v).strip()
                if t:
                    return t
            return ""

        agg = df.groupby("_uid", sort=False)["la_name"].agg(_first_name).reset_index()
        agg.columns = ["code", "name"]
    else:
        agg = df[["_uid"]].drop_duplicates("_uid").rename(columns={"_uid": "code"})
        agg["name"] = agg["code"]

    agg["name"] = agg.apply(
        lambda r: r["name"] if str(r["name"]).strip() else r["code"],
        axis=1,
    )
    agg["_sort_name"] = agg["name"].str.lower()
    agg = agg.sort_values(["_sort_name", "code"]).drop(columns=["_sort_name"])
    return agg.to_dict(orient="records")


@app.get("/la/{ladcd}/groups")
def get_groups(
    ladcd: str,
    test: bool = Query(default=False, description="Serve from data_test/ when true"),
    mode: str  = Query(default="local", description="Clustering mode: 'local' or 'national'"),
) -> list[str]:
    """Return the list of employment groups present for a given LA."""
    try:
        df = load_clusters(_clusters_path(test, mode))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    la_df = _rows_for_la(df, ladcd)
    if la_df.empty:
        raise HTTPException(status_code=404, detail=f"LA '{ladcd}' not found")

    return sorted(la_df["group"].dropna().unique().tolist())


@app.get("/la/{ladcd}/personas")
def get_personas(
    ladcd: str,
    group: str | None = Query(default=None, description="Filter by employment group"),
    test: bool = Query(default=False, description="Serve from data_test/ when true"),
    mode: str  = Query(default="local", description="Clustering mode: 'local' or 'national'"),
) -> list[dict[str, Any]]:
    """Return persona (tribe) rows for a given LA, optionally filtered by group."""
    try:
        df = load_clusters(_clusters_path(test, mode))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    la_df = _rows_for_la(df, ladcd)
    if la_df.empty:
        raise HTTPException(status_code=404, detail=f"LA '{ladcd}' not found")

    if group:
        la_df = la_df[la_df["group"] == group]
        if la_df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Group '{group}' not found for LA '{ladcd}'",
            )

    records = la_df.where(la_df.notna(), other=None).to_dict(orient="records")

    for rec in records:
        uid = rec.get("unit_id", "")
        tribe = rec.get("tribe_label", "")
        safe = re.sub(r'[^a-zA-Z0-9]+', '_', f"{uid}_{tribe}").strip('_').lower()
        fname = f"{safe}.png"
        if (PORTRAIT_DIR / fname).exists():
            rec["portrait_url"] = f"/portraits/{fname}"

    return records


# ---------------------------------------------------------------------------
# Static files — portraits, then frontend catch-all (MUST be last)
# ---------------------------------------------------------------------------

if PORTRAIT_DIR.exists():
    app.mount("/portraits", StaticFiles(directory=PORTRAIT_DIR), name="portraits")

_APP_DIR = _ROOT_DIR / "app"
if _APP_DIR.exists():
    app.mount("/", StaticFiles(directory=_APP_DIR, html=True), name="frontend")
