# data_processing/cluster_funcs.py
#
# Shared clustering and DNA-profile helpers used by:
#   6_cluster.ipynb               — global UKHLS tribe assignment
#   9_local_authority_cluster.ipynb — per-LA cluster profiles
#
# All functions are pure (no global state) and receive their config via arguments.

from __future__ import annotations

import numpy  as np
import pandas as pd
from sklearn.cluster import KMeans


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
        col = f"{wave}_{base_code}"
        if col not in subset.columns:
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
        elif series.dropna().isin([0.0, 1.0]).all():
            row[label] = f"{series.mean():.0%}"
        else:
            row[label] = round(series.mean(), 1)

    return row


# ── KMeans wrapper ────────────────────────────────────────────────────────────

def fit_kmeans(X: np.ndarray, k: int, random_state: int = 42) -> np.ndarray:
    """
    Fit KMeans with k-means++ init and return cluster labels.
    Falls back to a single cluster (all zeros) if k <= 1 or n < 2.
    """
    n = len(X)
    if k <= 1 or n < 2:
        return np.zeros(n, dtype=int)
    km = KMeans(n_clusters=k, init='k-means++', n_init=10, random_state=random_state)
    return km.fit_predict(X)


# ── Employment-group clustering ───────────────────────────────────────────────

def cluster_by_groups(
    df_features:      pd.DataFrame,
    df_profile:       pd.DataFrame,
    feature_cols:     list[str],
    groups:           dict,
    group_col_map:    dict[str, str | None],
    wave:             str,
    summary_vars:     list[str],
    variable_map:     dict[str, str],
    categorical_vars: set[str],
    category_maps:    dict[str, dict],
    k_default:        int = 2,
    min_cluster_size: int = 5,
) -> pd.DataFrame:
    """
    Split respondents by employment group, run KMeans within each group,
    and return a DNA DataFrame (one row per cluster tribe).

    Parameters
    ----------
    df_features   : DataFrame with pidp + normalised feature columns.
    df_profile    : DataFrame with pidp + real/raw columns used for DNA labels.
                    May be the same as df_features if features are sufficient.
    feature_cols  : Column names (with wave prefix) to pass to KMeans.
    groups        : config_cluster.GROUPS dict.
    group_col_map : { group_name → binary column name in df_features (or None for catch-all) }
    wave          : Wave prefix string, e.g. "o".
    summary_vars  : base codes to include in DNA rows (config_variables.SUMMARY_VARS).
    variable_map  : base_code → human label (config_variables.VARIABLE_MAP).
    categorical_vars : set of categorical base codes.
    category_maps : base_code → {numeric → label} (config_variables.CATEGORY_MAPS).
    k_default     : fallback k when group config omits "k".
    min_cluster_size : effective_k = min(k, n // min_cluster_size).

    Returns
    -------
    DataFrame sorted by size descending, one row per tribe.
    """
    dna_rows = []
    assigned = pd.Series(False, index=df_features.index)

    for gname, gcfg in groups.items():
        col = group_col_map.get(gname)

        if col and col in df_features.columns:
            mask = df_features[col] == 1.0
        elif col is None:
            mask = ~assigned   # "Other" catch-all
        else:
            continue

        group_feat    = df_features[mask]
        group_profile = df_profile[df_profile['pidp'].isin(group_feat['pidp'])]

        if group_feat.empty:
            continue
        assigned |= mask

        k           = gcfg.get('k', k_default)
        n           = len(group_feat)
        effective_k = min(k, max(1, n // min_cluster_size))
        labels      = fit_kmeans(group_feat[feature_cols].values, effective_k)

        group_feat = group_feat.copy()
        group_feat['_tribe_sub'] = labels

        for sub_id in sorted(group_feat['_tribe_sub'].unique()):
            sub_pidps = group_feat[group_feat['_tribe_sub'] == sub_id]['pidp']
            sub_prof  = group_profile[group_profile['pidp'].isin(sub_pidps)]
            label     = f"{gname} {sub_id + 1}" if effective_k > 1 else gname
            dna_rows.append(build_dna_row(
                label, sub_prof, wave,
                summary_vars, variable_map, categorical_vars, category_maps,
            ))

    if not dna_rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(dna_rows)
        .sort_values('size', ascending=False)
        .reset_index(drop=True)
    )
