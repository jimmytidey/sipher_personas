from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException

from app.demographic_mappings import (
    FIELD_LABELS,
    build_auto_value_mappings,
    decode_value,
    normalize_scalar,
    output_key,
    resolve_field_value,
)

BASE_DIR = Path(__file__).resolve().parents[1]
SIPHER_PATH = BASE_DIR / "data" / "sipher" / "pickles" / "sipher_optimized.pkl"
DEMOGRAPHICS_PATH = BASE_DIR / "data" / "ukhls" / "pickles" / "o_indresp_master_expanded.pkl"

rng = np.random.default_rng()

app = FastAPI(title="SIPHER Persona API", version="1.0.0")


@lru_cache(maxsize=1)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[Any, str]]]:
    if not SIPHER_PATH.exists():
        raise FileNotFoundError(f"Missing SIPHER file: {SIPHER_PATH}")
    if not DEMOGRAPHICS_PATH.exists():
        raise FileNotFoundError(f"Missing demographics file: {DEMOGRAPHICS_PATH}")

    sipher_df = pd.read_pickle(SIPHER_PATH)
    demographics_df = pd.read_pickle(DEMOGRAPHICS_PATH)

    if "pidp" not in sipher_df.columns:
        raise KeyError("SIPHER dataset is missing required column 'pidp'")
    if "pidp" not in demographics_df.columns:
        raise KeyError("Demographics dataset is missing required column 'pidp'")

    demographics_df = demographics_df.drop_duplicates(subset=["pidp"]).set_index("pidp", drop=False)
    matched_sipher = sipher_df[sipher_df["pidp"].isin(demographics_df.index)].reset_index(drop=True)
    auto_mappings = build_auto_value_mappings(demographics_df)

    if matched_sipher.empty:
        raise ValueError("No shared pidp values were found between SIPHER and demographics datasets")

    return matched_sipher, demographics_df, auto_mappings


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/persona/random")
def random_persona() -> dict[str, Any]:
    try:
        sipher_df, demographics_by_pidp, auto_mappings = load_data()
    except (FileNotFoundError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if sipher_df.empty:
        raise HTTPException(status_code=500, detail="SIPHER dataset is empty")

    random_index = int(rng.integers(0, len(sipher_df)))
    sipher_row = sipher_df.iloc[random_index]

    pidp = normalize_scalar(sipher_row.get("pidp"))
    if pidp is None:
        raise HTTPException(status_code=500, detail="Selected SIPHER row has invalid pidp")

    demographics_row = demographics_by_pidp.loc[pidp] if pidp in demographics_by_pidp.index else None
    if isinstance(demographics_row, pd.DataFrame):
        demographics_row = demographics_row.iloc[0]

    key_lookup = {column: output_key(column) for column in FIELD_LABELS}
    human_demographics: dict[str, Any] = {label: None for label in key_lookup.values()}

    if demographics_row is not None:
        for column in FIELD_LABELS:
            human_key = key_lookup[column]
            raw_value = resolve_field_value(column, demographics_row)
            human_demographics[human_key] = decode_value(column, raw_value, auto_mappings)

    response = {
        "sipher": {
            "synthetic_zone": normalize_scalar(sipher_row.get("synthetic_zone")),
            "pidp": pidp,
        },
        "demographics": human_demographics,
    }

    if demographics_row is None:
        response["demographics_note"] = "No matching demographics row found for this pidp"

    return response
