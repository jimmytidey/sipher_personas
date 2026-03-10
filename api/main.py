from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parents[1]
CLUSTERS_PATH = BASE_DIR / "data" / "6_cluster" / "LA_london_clusters.csv"
GEO_PATH = BASE_DIR / "data" / "0_raw" / "admin_geography_mappings.csv"

app = FastAPI(title="SIPHER Persona API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Data loaders (cached at startup)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_clusters() -> pd.DataFrame:
    if not CLUSTERS_PATH.exists():
        raise FileNotFoundError(f"Clusters file not found: {CLUSTERS_PATH}")
    return pd.read_csv(CLUSTERS_PATH)


@lru_cache(maxsize=1)
def load_la_names() -> dict[str, str]:
    """Return {ladcd: ladnm} from the geography lookup CSV."""
    if not GEO_PATH.exists():
        return {}
    geo = pd.read_csv(GEO_PATH, usecols=["ladcd", "ladnm"], encoding="latin-1")
    geo = geo.dropna(subset=["ladnm"])
    return geo.drop_duplicates("ladcd").set_index("ladcd")["ladnm"].to_dict()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/las")
def list_las() -> list[dict[str, str]]:
    """Return sorted list of all Local Authorities in the cluster data."""
    try:
        df = load_clusters()
        names = load_la_names()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    la_codes = sorted(df["unit_id"].dropna().unique().tolist())
    return [{"code": code, "name": names.get(code, code)} for code in la_codes]


@app.get("/la/{ladcd}/groups")
def get_groups(ladcd: str) -> list[str]:
    """Return the list of employment groups present for a given LA."""
    try:
        df = load_clusters()
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
) -> list[dict[str, Any]]:
    """Return persona (tribe) rows for a given LA, optionally filtered by group."""
    try:
        df = load_clusters()
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

    # Replace NaN with None for clean JSON serialisation
    return la_df.where(la_df.notna(), other=None).to_dict(orient="records")
