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

# ── Persona CSV (LA-scoped embedding k-means, step 8) ─────────────────────────
_CLUSTERS_DIR = BASE_DIR / "data" / "clusters"
PROD_EMBEDDING_CLUSTERS_PATH = _CLUSTERS_DIR / "LA_embedding_clusters.csv"
# Older pipeline builds used this filename; still accepted if the canonical file is missing.
LEGACY_EMBEDDING_CLUSTERS_PATH = _CLUSTERS_DIR / "LA_london_embedding_clusters.csv"

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


def _data_pipeline_folder() -> Path:
    """Project ``data/`` root for pipeline outputs."""
    try:
        import data_pipeline.config_variables as cv

        return _ROOT_DIR / cv.DATA_FOLDER
    except Exception:
        return _ROOT_DIR / "data"


def _embedding_cluster_csv_candidates() -> list[Path]:
    """
    Paths to try for embedding-mode persona CSVs, in order.

    Prefer api/data/clusters/ (deploy / committed copy), then pipeline output under
    data/…/8_embedding_clusters/ (step 8 output) so local dev works without manually copying.
    """
    candidates: list[Path] = [
        PROD_EMBEDDING_CLUSTERS_PATH,
        LEGACY_EMBEDDING_CLUSTERS_PATH,
    ]
    pipe_dir = _data_pipeline_folder() / "8_embedding_clusters"
    if pipe_dir.is_dir():
        for name in ("LA_embedding_clusters.csv", "LA_london_embedding_clusters.csv"):
            p = pipe_dir / name
            if p.exists():
                candidates.append(p)
        for p in sorted(pipe_dir.glob("LA*_embedding_clusters.csv")):
            if p not in candidates:
                candidates.append(p)

    seen: set[Path] = set()
    out: list[Path] = []
    for p in candidates:
        key = p.resolve()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _resolve_embedding_clusters_path() -> Path:
    """First existing embedding CSV (with described-file preference), else primary path."""
    for base in _embedding_cluster_csv_candidates():
        picked = _pick_cluster_csv(base)
        if picked.exists():
            return picked
    return PROD_EMBEDDING_CLUSTERS_PATH


def _pick_cluster_csv(base: Path) -> Path:
    """
    Prefer *_described.csv only when it exists and is not older than the base export.

    After re-exporting personas, the base CSV is refreshed but an old
    ``*_described.csv`` may still sit beside it — prefer the base file when described
    is stale (older mtime).
    """
    described = base.parent / (f"{base.stem}_described.csv")
    if not described.exists():
        return base
    if not base.exists():
        return described
    if described.stat().st_mtime >= base.stat().st_mtime:
        return described
    return base


def _clusters_path() -> Path:
    return _resolve_embedding_clusters_path()


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
def list_las() -> list[dict[str, str]]:
    """Return one entry per distinct unit_id in the cluster CSV (no separate LA master list)."""
    try:
        df = load_clusters(_clusters_path())
    except FileNotFoundError as exc:
        detail = (
            str(exc)
            + " — Run data_pipeline/8_cluster_embeddings.ipynb (step 8, LA mode); output is read from "
            "api/data/clusters/ or data/…/8_embedding_clusters/."
        )
        raise HTTPException(status_code=404, detail=detail) from exc

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
def get_groups(ladcd: str) -> list[str]:
    """Return the list of employment groups present for a given LA."""
    try:
        df = load_clusters(_clusters_path())
    except FileNotFoundError as exc:
        detail = (
            str(exc)
            + " — Run data_pipeline/8_cluster_embeddings.ipynb (step 8, LA mode); output is read from "
            "api/data/clusters/ or data/…/8_embedding_clusters/."
        )
        raise HTTPException(status_code=404, detail=detail) from exc

    la_df = _rows_for_la(df, ladcd)
    if la_df.empty:
        raise HTTPException(status_code=404, detail=f"LA '{ladcd}' not found")

    return sorted(la_df["group"].dropna().unique().tolist())


def _local_cluster_csv(cluster_type: str) -> Path:
    """Resolve path to the local-level cluster CSV for the given type.

    Prefers the api/data/clusters/ copy (written by notebooks 11/12) so that
    deployment works without the full pipeline data folder being present.
    Falls back to the pipeline output folder for local dev.
    """
    _VALID = ("embedding", "values", "llm_gemini", "llm_claude")
    if cluster_type not in _VALID:
        raise HTTPException(status_code=400, detail=f"cluster_type must be one of {_VALID}")

    filename = f"local_{cluster_type}_clusters.csv"

    # 1. Prefer api/data/clusters/ (deploy copy)
    api_copy = _CLUSTERS_DIR / filename
    if api_copy.exists():
        return api_copy

    # 2. Fall back to pipeline output folder
    pipe_data = _data_pipeline_folder()
    step_dirs = {
        "embedding":  pipe_data / "11_cluster_embeddings_LA" / "la_embedding_clusters.csv",
        "values":     pipe_data / "12_cluster_values_LA"    / "la_values_clusters.csv",
        "llm_gemini": pipe_data / "api" / "data" / "clusters" / "local_llm_gemini_clusters.csv",
        "llm_claude":  pipe_data / "api" / "data" / "clusters" / "local_llm_claude_clusters.csv",
    }
    return step_dirs[cluster_type]


@app.get("/local-las")
def local_las(
    cluster_type: str = Query(default="embedding", description="'embedding', 'values', 'llm_gemini', or 'llm_claude'"),
) -> list[dict[str, str]]:
    """Return the list of LAs available in the local cluster output for the given type."""
    csv_path = _local_cluster_csv(cluster_type)
    if not csv_path.exists():
        step_map = {"embedding": "11", "values": "12", "llm_gemini": "14", "llm_claude": "15"}
        raise HTTPException(
            status_code=404,
            detail=(
                f"{csv_path} not found. "
                f"Run data_pipeline/{step_map.get(cluster_type, '?')}_*.ipynb to generate it."
            ),
        )
    df = pd.read_csv(csv_path, usecols=["ladcd", "ladnm"], dtype=str)
    agg = (
        df.drop_duplicates("ladcd")
        .sort_values("ladnm")
        .rename(columns={"ladcd": "code", "ladnm": "name"})
    )
    return agg.to_dict(orient="records")


@app.get("/local-clusters")
def local_clusters(
    ladcd: str = Query(..., description="LA code, e.g. E09000030"),
    cluster_type: str = Query(default="embedding", description="'embedding', 'values', 'llm_gemini', or 'llm_claude'"),
) -> list[dict[str, Any]]:
    """
    Per-cluster summary for one Local Authority.

    Reads the local-level cluster CSV (step 11, 12, 14, or 15) and aggregates by cluster:
      cluster_id, ladcd, ladnm, tribe_label, tribe_description, n_respondents, size (synthetic pop)
    """
    csv_path = _local_cluster_csv(cluster_type)
    if not csv_path.exists():
        step_map = {"embedding": "11", "values": "12", "llm_gemini": "14", "llm_claude": "15"}
        raise HTTPException(
            status_code=404,
            detail=(
                f"{csv_path} not found. "
                f"Run data_pipeline/{step_map.get(cluster_type, '?')}_*.ipynb to generate it."
            ),
        )

    df = pd.read_csv(csv_path, dtype={"ladcd": str, "ladnm": str})
    la_df = df[df["ladcd"] == ladcd].copy()
    if la_df.empty:
        raise HTTPException(status_code=404, detail=f"LA '{ladcd}' not found in {csv_path.name}")

    total_pop = la_df["size"].sum() if "size" in la_df.columns else 0
    if total_pop > 0:
        la_df["pct_of_la"] = (la_df["size"] / total_pop * 100).round(1)

    return la_df.where(la_df.notna(), other=None).to_dict(orient="records")


@app.get("/national-clusters")
def national_clusters(
    cluster_type: str = Query(default="embedding", description="'embedding', 'values', or 'llm'"),
) -> list[dict[str, Any]]:
    """
    National-level cluster summaries.

    Reads a pre-aggregated CSV written by the pipeline:
      api/data/clusters/national_embedding_clusters.csv  (step 8)
      api/data/clusters/national_values_clusters.csv     (step 9)
      api/data/clusters/national_llm_clusters.csv        (step 11)

    Re-run the relevant notebook to refresh after rerunning the pipeline.
    """
    _VALID = ("embedding", "values", "llm")
    if cluster_type not in _VALID:
        raise HTTPException(status_code=400, detail=f"cluster_type must be one of {_VALID}")

    csv_name = f"national_{cluster_type}_clusters.csv"
    csv_path = _CLUSTERS_DIR / csv_name

    if not csv_path.exists():
        step_map = {"embedding": "8", "values": "9", "llm": "11"}
        raise HTTPException(
            status_code=404,
            detail=(
                f"{csv_path} not found. "
                f"Run data_pipeline/{step_map[cluster_type]}_*.ipynb to generate it."
            ),
        )

    df = pd.read_csv(csv_path)
    return df.where(df.notna(), other=None).to_dict(orient="records")


@app.get("/la/{ladcd}/personas")
def get_personas(
    ladcd: str,
    group: str | None = Query(default=None, description="Filter by employment group"),
) -> list[dict[str, Any]]:
    """Return persona (tribe) rows for a given LA, optionally filtered by group."""
    try:
        df = load_clusters(_clusters_path())
    except FileNotFoundError as exc:
        detail = (
            str(exc)
            + " — Run data_pipeline/8_cluster_embeddings.ipynb (step 8, LA mode); output is read from "
            "api/data/clusters/ or data/…/8_embedding_clusters/."
        )
        raise HTTPException(status_code=404, detail=detail) from exc

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


@app.get("/pipeline-status")
def pipeline_status() -> dict[str, Any]:
    """
    Return the number of distinct LAs processed for each local cluster type.

    Used by the frontend to render a pipeline progress panel.
    """
    _LOCAL_TYPES: dict[str, str] = {
        "embedding":  "local_embedding_clusters.csv",
        "values":     "local_values_clusters.csv",
        "llm_gemini": "local_llm_gemini_clusters.csv",
        "llm_claude": "local_llm_claude_clusters.csv",
    }
    result: dict[str, Any] = {}
    max_las = 0
    for t, fname in _LOCAL_TYPES.items():
        path = _CLUSTERS_DIR / fname
        if path.exists():
            try:
                df = pd.read_csv(path, usecols=["ladcd"], dtype=str)
                la_count = int(df["ladcd"].nunique())
            except Exception:
                la_count = 0
        else:
            la_count = 0
        result[t] = la_count
        if la_count > max_las:
            max_las = la_count
    result["_total"] = max_las   # largest count = reference denominator
    return result


# ---------------------------------------------------------------------------
# Static files — portraits, then frontend catch-all (MUST be last)
# ---------------------------------------------------------------------------

if PORTRAIT_DIR.exists():
    app.mount("/portraits", StaticFiles(directory=PORTRAIT_DIR), name="portraits")

_APP_DIR = _ROOT_DIR / "app"
if _APP_DIR.exists():
    app.mount("/", StaticFiles(directory=_APP_DIR, html=True), name="frontend")
