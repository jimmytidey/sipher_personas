# data_pipeline/helpers/cluster.py
#
# Shared clustering and DNA-profile helpers used by embedding persona export
# (step 8 — 8_cluster_embeddings.ipynb) and related steps.
#
# All functions are pure (no global state) and receive their config via arguments.

from __future__ import annotations

import numpy  as np
import pandas as pd
from sklearn.cluster  import KMeans

try:
    from data_pipeline.config_variables import preferred_summary_column
except ModuleNotFoundError:  # pragma: no cover
    from config_variables import preferred_summary_column


# ── DNA helpers ───────────────────────────────────────────────────────────────

def get_mode(series: pd.Series) -> float:
    """Return the modal value of a numeric series, or NaN if empty."""
    m = series.dropna().mode()
    return float(m.iloc[0]) if not m.empty else np.nan


def build_dna_row(
    tribe_label:  str,
    subset:       pd.DataFrame,
    wave:         str,
    summary_vars: list[str],
    variable_map: dict[str, str],
    categorical_vars: set[str],
    category_maps:    dict[str, dict],
    continuous_vars:  set[str] | None = None,
) -> dict:
    """
    Build one row of a DNA persona table from a subset of respondents.

    For continuous variables   → mean (rounded to 1 dp).
    For binary (0/1) variables → percentage string.
    For categorical variables  → modal category label.
    For jbstat                 → top-3 breakdown string.
    """
    row: dict = {'tribe_label': tribe_label, 'size': len(subset)}

    for base_code in summary_vars:
        col = preferred_summary_column(wave, base_code, subset.columns)
        if col is None:
            continue
        label  = variable_map.get(base_code, base_code)
        series = pd.to_numeric(subset[col], errors='coerce')

        if base_code in categorical_vars and base_code in category_maps and category_maps[base_code]:
            cat_map  = category_maps[base_code]
            mode_val = get_mode(series)
            if base_code == 'jbstat':
                counts = series.value_counts(normalize=True)
                parts  = [f"{cat_map.get(c, c)}: {v:.0%}" for c, v in counts.head(3).items()]
                row[label] = ' | '.join(parts)
            else:
                row[label] = cat_map.get(mode_val, str(mode_val))
                pct = None
                if not pd.isna(mode_val):
                    counts = series.value_counts(normalize=True)
                    pct = round(counts.get(mode_val, 0) * 100)
                row[label + " %"] = pct
        elif base_code not in (continuous_vars or set()) and series.dropna().isin([0.0, 1.0]).all():
            row[label] = f"{series.mean():.0%}"
        else:
            row[label] = round(series.mean(), 1)

    return row


# ── KMeans wrapper ────────────────────────────────────────────────────────────

def fit_kmeans(
    X:            np.ndarray,
    k:            int,
    random_state: int = 42,
    sample_weight: np.ndarray | None = None,
) -> np.ndarray:
    """
    Fit KMeans with k-means++ init and return cluster labels.
    Falls back to a single cluster (all zeros) if k <= 1 or n < 2.
    """
    n = len(X)
    if k <= 1 or n < 2:
        return np.zeros(n, dtype=int)
    km = KMeans(n_clusters=k, init='k-means++', n_init=3, random_state=random_state)
    return km.fit_predict(X, sample_weight=sample_weight)

