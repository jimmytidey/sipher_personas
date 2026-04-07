# data_pipeline/helpers/normalise.py
#
# Lightweight Z-score normalisation expressed as per-variable Mx + c coefficients:
#
#   x_normalised = M * x + c
#   where  M = 1 / std,  c = -mean / std
#
# This is algebraically identical to StandardScaler but the coefficients are
# explicit scalars that can be inspected, saved, and applied to any DataFrame
# (e.g. the synthetic population) without re-fitting.

from __future__ import annotations

import pickle
from pathlib import Path
from typing  import Dict, Tuple

import numpy  as np
import pandas as pd

# Coefficient dict type: { column_name → (M, c) }
Coefficients = Dict[str, Tuple[float, float]]


def fit(df: pd.DataFrame, cols: list[str]) -> Coefficients:
    """
    Fit Mx+c coefficients from a DataFrame.

    Parameters
    ----------
    df   : DataFrame containing the columns to fit.
    cols : Column names to fit (typically ``expected_cluster_feature_columns(wave)``
           from config_variables — raw or OHE-expanded — matching the K-Means design matrix).

    Returns
    -------
    dict { col → (M, c) } where x_norm = M * x + c.
    Columns with zero std (constant) get M=1, c=0 (left unchanged).
    """
    coeffs: Coefficients = {}
    for col in cols:
        series = pd.to_numeric(df[col], errors='coerce').dropna()
        mu     = float(series.mean())
        sigma  = float(series.std(ddof=0))
        if sigma == 0:
            coeffs[col] = (1.0, 0.0)
        else:
            coeffs[col] = (1.0 / sigma, -mu / sigma)
    return coeffs


def apply(df: pd.DataFrame, coeffs: Coefficients, fill_na: float = 0.0) -> pd.DataFrame:
    """
    Apply pre-fitted Mx+c coefficients to a DataFrame.

    Columns not present in `coeffs` are left unchanged.
    NaN values are filled with `fill_na` after scaling (default 0, the Z-score mean).

    Returns a copy — the original is not modified.
    """
    df = df.copy()
    for col, (M, c) in coeffs.items():
        if col not in df.columns:
            continue
        numeric    = pd.to_numeric(df[col], errors='coerce')
        df[col]    = (numeric * M + c).fillna(fill_na)
    return df


def save(coeffs: Coefficients, path: str | Path) -> None:
    """Persist coefficients to a pickle file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as fh:
        pickle.dump(coeffs, fh, protocol=pickle.HIGHEST_PROTOCOL)


def load(path: str | Path) -> Coefficients:
    """Load coefficients previously saved with save()."""
    with open(path, 'rb') as fh:
        return pickle.load(fh)


def summary(coeffs: Coefficients) -> pd.DataFrame:
    """Return a readable DataFrame of all Mx+c coefficients."""
    rows = [{'column': col, 'M': M, 'c': c, 'mean': -c / M if M != 0 else 0, 'std': 1 / M if M != 0 else 1}
            for col, (M, c) in coeffs.items()]
    return pd.DataFrame(rows).set_index('column')
