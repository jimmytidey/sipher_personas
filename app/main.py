from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException

BASE_DIR = Path(__file__).resolve().parents[1]
SIPHER_PATH = BASE_DIR / "data" / "sipher" / "pickles" / "sipher_optimized.pkl"
DEMOGRAPHICS_PATH = BASE_DIR / "data" / "ukhls" / "pickles" / "o_indresp_optimized.pkl"

FIELD_LABELS = {
    "o_sex": "sex",
    "o_dvage": "age",
    "o_birthy": "birth_year",
    "o_racel_dv": "ethnicity",
    "o_jbstat": "employment_status",
    "o_mastat_dv": "marital_status",
    "o_hiqual_dv": "highest_qualification",
}

MISSING_CODES = {-1, -2, -7, -8, -9}

CODEBOOKS: dict[str, dict[int, str]] = {
    "o_sex": {
        1: "Male",
        2: "Female",
    },
    "o_racel_dv": {
        1: "White British",
        2: "White Irish",
        3: "White Other",
        4: "Mixed: White and Black Caribbean",
        5: "Mixed: White and Black African",
        6: "Mixed: White and Asian",
        7: "Mixed: Other",
        8: "Indian",
        9: "Pakistani",
        10: "Bangladeshi",
        11: "Chinese",
        12: "Asian Other",
        13: "Black Caribbean",
        14: "Black African",
        15: "Black Other",
        16: "Arab",
        17: "Other ethnic group",
    },
    "o_jbstat": {
        1: "Self-employed",
        2: "Employed",
        3: "Unemployed",
        4: "Retired",
        5: "On maternity leave",
        6: "Family care or home",
        7: "Full-time student",
        8: "Long-term sick or disabled",
        9: "Government training scheme",
        10: "Unpaid family business",
        11: "Apprenticeship",
        12: "Temporarily laid off",
        13: "Other",
    },
    "o_mastat_dv": {
        1: "Married",
        2: "Single",
        3: "Separated",
        4: "Divorced",
        5: "Widowed",
        6: "Civil partnership",
        7: "Former civil partnership",
        8: "Surviving civil partner",
        9: "Cohabiting",
        10: "In a relationship",
    },
    "o_hiqual_dv": {
        1: "Degree",
        2: "Higher education below degree",
        3: "A-level or equivalent",
        4: "GCSE or equivalent",
        5: "Other qualification",
        9: "No qualification",
    },
}

rng = np.random.default_rng()

app = FastAPI(title="SIPHER Persona API", version="1.0.0")


def _normalize_scalar(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer, int)):
        as_int = int(value)
        return None if as_int in MISSING_CODES else as_int
    if isinstance(value, (np.floating, float)):
        if float(value).is_integer():
            as_int = int(value)
            return None if as_int in MISSING_CODES else as_int
        return float(value)
    return value


def _decode_value(column: str, value: Any) -> Any:
    normalized = _normalize_scalar(value)
    if normalized is None:
        return None
    if column in CODEBOOKS and isinstance(normalized, int):
        return CODEBOOKS[column].get(normalized, f"Unknown code ({normalized})")
    return normalized


@lru_cache(maxsize=1)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
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

    if matched_sipher.empty:
        raise ValueError("No shared pidp values were found between SIPHER and demographics datasets")

    return matched_sipher, demographics_df


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/persona/random")
def random_persona() -> dict[str, Any]:
    try:
        sipher_df, demographics_by_pidp = load_data()
    except (FileNotFoundError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if sipher_df.empty:
        raise HTTPException(status_code=500, detail="SIPHER dataset is empty")

    random_index = int(rng.integers(0, len(sipher_df)))
    sipher_row = sipher_df.iloc[random_index]

    pidp = _normalize_scalar(sipher_row.get("pidp"))
    if pidp is None:
        raise HTTPException(status_code=500, detail="Selected SIPHER row has invalid pidp")

    demographics_row = demographics_by_pidp.loc[pidp] if pidp in demographics_by_pidp.index else None
    if isinstance(demographics_row, pd.DataFrame):
        demographics_row = demographics_row.iloc[0]

    human_demographics: dict[str, Any] = {}
    raw_demographics: dict[str, Any] = {}

    if demographics_row is not None:
        for column in demographics_row.index:
            raw_value = _normalize_scalar(demographics_row[column])
            raw_demographics[column] = raw_value

            output_key = FIELD_LABELS.get(column, column)
            human_demographics[output_key] = _decode_value(column, demographics_row[column])

    response = {
        "sipher": {
            "synthetic_zone": _normalize_scalar(sipher_row.get("synthetic_zone")),
            "pidp": pidp,
        },
        "demographics": human_demographics,
        "raw_codes": raw_demographics,
    }

    if demographics_row is None:
        response["demographics_note"] = "No matching demographics row found for this pidp"

    return response
