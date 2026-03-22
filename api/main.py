from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

_API_DIR  = Path(__file__).resolve().parent
_ROOT_DIR = _API_DIR.parent
# Use api/data/ when it exists (self-contained deployment), else fall back to project root
BASE_DIR = _API_DIR if (_API_DIR / "data").exists() else _ROOT_DIR

PORTRAIT_DIR = _API_DIR / "data" / "portraits"

# Production paths
PROD_CLUSTERS_PATH = BASE_DIR / "data" / "clusters" / "LA_london_clusters.csv"

# Test paths  (data_test/ folder, built from test_config_variables)
TEST_CLUSTERS_PATH = BASE_DIR / "data_test" / "6_cluster" / "LA_clusters.csv"

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


def _clusters_path(test: bool) -> Path:
    clusters = TEST_CLUSTERS_PATH if test else PROD_CLUSTERS_PATH
    # Prefer the GPT-described version when it exists
    described = clusters.parent / (clusters.stem + "_described.csv")
    return described if described.exists() else clusters


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/las")
def list_las(
    test: bool = Query(default=False, description="Serve from data_test/ when true"),
) -> list[dict[str, str]]:
    """Return sorted list of all Local Authorities in the cluster data."""
    try:
        df = load_clusters(_clusters_path(test))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    name_map = (
        df[["unit_id", "la_name"]].drop_duplicates("unit_id").set_index("unit_id")["la_name"].to_dict()
        if "la_name" in df.columns else {}
    )
    la_codes = sorted(df["unit_id"].dropna().unique().tolist())
    return [{"code": code, "name": name_map.get(code, code)} for code in la_codes]


@app.get("/la/{ladcd}/groups")
def get_groups(
    ladcd: str,
    test: bool = Query(default=False, description="Serve from data_test/ when true"),
) -> list[str]:
    """Return the list of employment groups present for a given LA."""
    try:
        df = load_clusters(_clusters_path(test))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    la_df = df[df["unit_id"] == ladcd]
    if la_df.empty:
        raise HTTPException(status_code=404, detail=f"LA '{ladcd}' not found")

    return sorted(la_df["group"].dropna().unique().tolist())


@app.get("/la/{ladcd}/personas")
def get_personas(
    ladcd: str,
    group: str | None = Query(default=None, description="Filter by employment group"),
    test: bool = Query(default=False, description="Serve from data_test/ when true"),
) -> list[dict[str, Any]]:
    """Return persona (tribe) rows for a given LA, optionally filtered by group."""
    try:
        df = load_clusters(_clusters_path(test))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    la_df = df[df["unit_id"] == ladcd]
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
