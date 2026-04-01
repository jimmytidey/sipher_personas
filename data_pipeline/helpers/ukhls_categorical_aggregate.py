# data_pipeline/helpers/ukhls_categorical_aggregate.py
#
# Aggregate UKHLS reference tables (e.g. raw ethnicity codes) to collapsed codes
# using the same recode maps as feature engineering.

from __future__ import annotations

from pathlib import Path

import pandas as pd


def pipeline_reference_dir() -> Path:
    """``data_pipeline/reference`` — anchored to this package (works regardless of notebook cwd)."""
    return Path(__file__).resolve().parent.parent / "reference"


def racel_collapsed_percent_from_raw(raw_path: Path, recode: dict) -> dict[float, float]:
    """Sum ``percent`` in ``racel_raw_ukhl.csv`` by collapsed group.

    Uses the same mapping as feature engineering: ``RECODE_MAPS[\"racel_dv\"]`` from
    ``config_variables`` (defined in ``config_variables_demographics.racel_dv`` → ``recode``).

    Keys are normalised to float so lookups match CSV values and config literals.
    """
    if not raw_path.exists():
        return {}
    # Same dict as 4a: { raw racel_dv code -> collapsed group code (0–9) }
    recode_f = {float(k): float(v) for k, v in recode.items()}
    df = pd.read_csv(raw_path)
    out: dict[float, float] = {}
    for _, row in df.iterrows():
        raw_code = float(row["category_code"])
        p = row.get("percent")
        if pd.isna(p):
            continue
        collapsed = recode_f.get(raw_code)
        if collapsed is None:
            continue
        collapsed = float(collapsed)
        out[collapsed] = out.get(collapsed, 0.0) + float(p)
    return out
