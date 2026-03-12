from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parents[1]

# Production paths
PROD_CLUSTERS_PATH = BASE_DIR / "data" / "6_cluster" / "LA_london_clusters.csv"
PROD_GEO_PATH      = BASE_DIR / "data" / "0_raw" / "admin_geography_mappings.csv"

# Test paths  (data_test/ folder, built from test_config_variables)
TEST_CLUSTERS_PATH = BASE_DIR / "data_test" / "6_cluster" / "LA_clusters.csv"
TEST_GEO_PATH      = BASE_DIR / "data_test" / "0_raw" / "admin_geography_mappings.csv"

app = FastAPI(title="SIPHER Persona API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Data loaders — cached per path so prod and test coexist in memory
# ---------------------------------------------------------------------------

@lru_cache(maxsize=4)
def load_clusters(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Clusters file not found: {path}")
    return pd.read_csv(path)


@lru_cache(maxsize=4)
def load_la_names(path: Path) -> dict[str, str]:
    """Return {ladcd: ladnm} from the geography lookup CSV."""
    if not path.exists():
        return {}
    geo = pd.read_csv(path, usecols=["ladcd", "ladnm"], encoding="latin-1")
    geo = geo.dropna(subset=["ladnm"])
    return geo.drop_duplicates("ladcd").set_index("ladcd")["ladnm"].to_dict()


def _paths(test: bool) -> tuple[Path, Path]:
    return (TEST_CLUSTERS_PATH, TEST_GEO_PATH) if test else (PROD_CLUSTERS_PATH, PROD_GEO_PATH)


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
    clusters_path, geo_path = _paths(test)
    try:
        df    = load_clusters(clusters_path)
        names = load_la_names(geo_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    la_codes = sorted(df["unit_id"].dropna().unique().tolist())
    return [{"code": code, "name": names.get(code, code)} for code in la_codes]


@app.get("/la/{ladcd}/groups")
def get_groups(
    ladcd: str,
    test: bool = Query(default=False, description="Serve from data_test/ when true"),
) -> list[str]:
    """Return the list of employment groups present for a given LA."""
    clusters_path, _ = _paths(test)
    try:
        df = load_clusters(clusters_path)
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
    clusters_path, _ = _paths(test)
    try:
        df = load_clusters(clusters_path)
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
