from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

MISSING_CODES = {
    -1: "Missing: Don't know",
    -2: "Missing: Refused",
    -7: "Missing: Proxy",
    -8: "Missing: Inapplicable",
    -9: "Missing: Not asked",
}

FIELD_LABELS = {
    "o_age_dv": "Age",
    "o_sex_dv": "Gender",
    "o_jbstat": "Employment Status",
    "o_payn_dv": "Monthly Net Pay",
    "o_hiqual_dv": "Education",
    "o_health": "General Health",
    "o_hllt": "Health Limits Daily Activities",
    "o_disdiff": "Health Impairment Type",
    "o_scghq1_dv": "Mental Distress",
    "o_sf1": "Life Satisfaction",
    "o_lnp1": "First Language",
    "o_lneng": "English Ability",
    "o_lnhome": "Language Spoken at Home",
    "o_caruse": "Car Use Frequency",
    "o_commute": "Commute Time",
    "o_traffic": "Traffic Stress",
    "o_traccess": "Public Transport Access",
    "o_ncar": "Number of Cars in Household",
}

DISABILITY_TYPE_INDICATORS = {
    "o_disdif1": "Mobility",
    "o_disdif2": "Lifting, carrying or moving objects",
    "o_disdif3": "Manual dexterity",
    "o_disdif4": "Continence",
    "o_disdif5": "Hearing",
    "o_disdif6": "Vision",
    "o_disdif7": "Memory or ability to concentrate, learn or understand",
    "o_disdif8": "Recognising physical danger",
    "o_disdif9": "Coordination",
    "o_disdif10": "Speech",
    "o_disdif11": "Mental health",
    "o_disdif12": "Stamina or breathing or fatigue",
    "o_disdif96": "Other impairment",
}

VALUE_MAPPINGS: dict[str, dict[int, str]] = {
    "o_sex_dv": {
        1: "Male",
        2: "Female",
    },
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
    "o_hllt": {
        1: "A lot",
        2: "A little",
    },
    "o_caruse": {
        1: "Uses car",
        2: "Does not use car",
    },
    "o_traccess": {
        1: "Very easy",
        2: "Easy",
        3: "Neither easy nor difficult",
        4: "Difficult",
        5: "Very difficult",
    },
}

PASSTHROUGH_COLUMNS = {
    "o_age_dv",
    "o_payn_dv",
    "o_scghq1_dv",
    "o_sf1",
    "o_commute",
    "o_traffic",
    "o_ncar",
}


def resolve_field_value(field: str, demographics_row: pd.Series) -> Any:
    if field == "o_disdiff":
        active_impairments: list[str] = []
        for indicator_column, label in DISABILITY_TYPE_INDICATORS.items():
            if indicator_column not in demographics_row.index:
                continue
            indicator_value = normalize_scalar(demographics_row[indicator_column])
            if indicator_value == 1:
                active_impairments.append(label)

        if active_impairments:
            return ", ".join(active_impairments)
        return None

    if field in demographics_row.index:
        return demographics_row[field]

    return None


def normalize_scalar(value: Any) -> Any:
    if pd.isna(value):
        return None

    if isinstance(value, (np.integer, int)):
        as_int = int(value)
        if as_int in MISSING_CODES:
            return MISSING_CODES[as_int]
        return as_int

    if isinstance(value, (np.floating, float)):
        as_float = float(value)
        if as_float.is_integer():
            as_int = int(as_float)
            if as_int in MISSING_CODES:
                return MISSING_CODES[as_int]
            return as_int
        return as_float

    if isinstance(value, (np.bool_, bool)):
        return bool(value)

    return value


def build_auto_value_mappings(df: pd.DataFrame, max_unique: int = 200) -> dict[str, dict[Any, str]]:
    auto_mappings: dict[str, dict[Any, str]] = {}

    for column in df.columns:
        if column in VALUE_MAPPINGS:
            continue

        series = df[column].dropna()
        if series.empty:
            continue

        if pd.api.types.is_numeric_dtype(series):
            normalized_unique = sorted(
                {
                    int(value)
                    for value in series.unique()
                    if float(value).is_integer() and int(value) not in MISSING_CODES
                }
            )

            if normalized_unique and len(normalized_unique) <= max_unique:
                auto_mappings[column] = {value: f"Code {value}" for value in normalized_unique}

    return auto_mappings


def decode_value(column: str, value: Any, auto_mappings: dict[str, dict[Any, str]] | None = None) -> Any:
    normalized = normalize_scalar(value)
    if normalized is None:
        return None

    if column in PASSTHROUGH_COLUMNS:
        return normalized

    if isinstance(normalized, str) and normalized.startswith("Missing:"):
        return normalized

    manual_map = VALUE_MAPPINGS.get(column, {})
    if normalized in manual_map:
        return manual_map[normalized]

    if auto_mappings and column in auto_mappings and normalized in auto_mappings[column]:
        return auto_mappings[column][normalized]

    identifier_tokens = ("pid", "hid", "pno", "psu", "strata", "orig")
    if isinstance(normalized, int) and not any(token in column.lower() for token in identifier_tokens):
        return f"Code {normalized}"

    return normalized


def _humanize_column_name(column: str) -> str:
    if column in FIELD_LABELS:
        return FIELD_LABELS[column]

    cleaned = column.strip().lower()

    if len(cleaned) > 2 and cleaned[1] == "_" and cleaned[0].isalpha():
        cleaned = cleaned[2:]

    replacements = {
        "_dv": " derived",
        "_": " ",
    }

    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)

    cleaned = " ".join(cleaned.split())
    return cleaned


def output_key(column: str, used_keys: set[str] | None = None) -> str:
    base_key = _humanize_column_name(column)

    if used_keys is None:
        return base_key

    candidate = base_key
    suffix = 2
    while candidate in used_keys:
        candidate = f"{base_key} ({suffix})"
        suffix += 1

    used_keys.add(candidate)
    return candidate
