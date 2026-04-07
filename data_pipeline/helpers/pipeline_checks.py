# data_pipeline/helpers/pipeline_checks.py
#
# Light-weight dataframe audits at the end of pipeline steps.

from __future__ import annotations

import numpy as np
import pandas as pd


def warn_non_numeric(
    df: pd.DataFrame,
    step: str,
    *,
    ignore_cols: set[str] | frozenset[str] | None = None,
) -> None:
    """Audit dtypes/inf, then report per-column NaN counts (same ``ignore_cols`` for both).

    ``ignore_cols`` is skipped for dtype/inf and for the NaN listing (e.g. geography strings).
    Categorical dtypes are not flagged as non-numeric.
    """
    ignore = frozenset(ignore_cols or ())
    issues: list[str] = []
    n_rows = len(df)

    for col in df.columns:
        if col in ignore:
            continue
        s = df[col]
        if pd.api.types.is_object_dtype(s):
            issues.append(f"  {col}: dtype=object")
        elif pd.api.types.is_string_dtype(s):
            issues.append(f"  {col}: dtype=string")
        elif pd.api.types.is_bool_dtype(s):
            issues.append(f"  {col}: dtype=bool")
        elif pd.api.types.is_float_dtype(s):
            arr = pd.to_numeric(s, errors="coerce").to_numpy(dtype=np.float64)
            inf_mask = np.isinf(arr)
            if inf_mask.any():
                issues.append(f"  {col}: {int(inf_mask.sum()):,} inf values")

    print(f"\n--- Non-numeric / inf audit [{step}] ---")
    if issues:
        print("WARNING — unexpected non-numeric dtypes or inf in floats:")
        print("\n".join(issues))
    else:
        print("OK — no object/string/bool columns; no inf in float columns (respecting ignore_cols).")

    nan_lines: list[str] = []
    for col in df.columns:
        if col in ignore:
            continue
        n_na = int(df[col].isna().sum())
        if n_na > 0:
            pct = 100.0 * n_na / n_rows if n_rows else 0.0
            nan_lines.append(f"  {col}: {n_na:,} missing ({pct:.1f}% of rows)")

    print(f"\n--- NaN / missing audit [{step}] ---")
    if nan_lines:
        print(f"Columns with missing values ({len(nan_lines)} of {len(df.columns)} checked):")
        print("\n".join(nan_lines))
    else:
        print("OK — no NaN/NA in checked columns.")
