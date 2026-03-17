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
from sklearn.cluster  import KMeans
from sklearn.metrics  import silhouette_score


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
        elif base_code not in (continuous_vars or set()) and series.dropna().isin([0.0, 1.0]).all():
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


def best_k_by_silhouette(
    X:              np.ndarray,
    max_k:          int,
    min_silhouette: float = 0.05,
    random_state:   int   = 42,
) -> int:
    """
    Try k = 2..max_k and return the k that maximises silhouette score.

    Returns 1 if no k achieves a score >= min_silhouette, meaning the data
    has no meaningful cluster structure beyond a single group.

    Parameters
    ----------
    X              : feature matrix (already normalised).
    max_k          : upper bound (typically min(group_k, n // min_cluster_size)).
    min_silhouette : minimum silhouette score required to prefer k > 1.
                     0.05 is a deliberately low bar — raise to e.g. 0.15 to
                     require more clearly separated clusters.
    """
    n = len(X)
    if max_k <= 1 or n < 4:
        return 1

    best_k     = 1
    best_score = min_silhouette  # must beat this floor to win

    for k in range(2, min(max_k, n // 2) + 1):
        km     = KMeans(n_clusters=k, init='k-means++', n_init=10, random_state=random_state)
        labels = km.fit_predict(X)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(X, labels, sample_size=min(5_000, n), random_state=random_state)
        if score > best_score:
            best_score = score
            best_k     = k

    return best_k


# ── Employment-group clustering ───────────────────────────────────────────────

def cluster_by_groups(
    df_features:        pd.DataFrame,
    df_profile:         pd.DataFrame,
    feature_cols:       list[str],
    groups:             list[str],
    group_col_map:      dict[str, str | None],
    wave:               str,
    summary_vars:       list[str],
    variable_map:       dict[str, str],
    categorical_vars:   set[str],
    category_maps:      dict[str, dict],
    max_total_clusters: int   = 10,
    min_cluster_size:   int   = 5,
    continuous_vars:    set[str] | None = None,
    min_silhouette:     float = 0.05,
) -> pd.DataFrame:
    """
    Split respondents by employment group, run KMeans within each group,
    and return a DNA DataFrame (one row per cluster tribe).

    Parameters
    ----------
    df_features         : DataFrame with pidp + normalised feature columns.
    df_profile          : DataFrame with pidp + real/raw columns for DNA labels.
    feature_cols        : Column names (with wave prefix) to pass to KMeans.
    groups              : Ordered list of group names (config_cluster.GROUPS).
    group_col_map       : { group_name → binary OHE column, or None for catch-all }
    wave                : Wave prefix string, e.g. "o".
    summary_vars        : base codes to include in DNA rows.
    variable_map        : base_code → human label.
    categorical_vars    : set of categorical base codes.
    category_maps       : base_code → {numeric → label}.
    max_total_clusters  : total cluster budget shared across all groups;
                          each group's k = max(1, round(budget * n_group / n_total)).
    min_cluster_size    : caps effective_k to n // min_cluster_size.
    min_silhouette      : silhouette score floor; if no k > 1 beats this,
                          the group is kept as a single cluster (k=1).
                          Set to 0.0 to always use the full proportional k.

    Returns
    -------
    DataFrame sorted by size descending, one row per tribe.
    """
    # ── Pass 1: measure group sizes to allocate k proportionally ─────────────
    assigned   = pd.Series(False, index=df_features.index)
    group_masks: dict[str, pd.Series] = {}
    group_sizes: dict[str, int]       = {}

    for gname in groups:
        col = group_col_map.get(gname)
        if col and col in df_features.columns:
            mask = df_features[col] == 1.0
        elif col is None:
            mask = ~assigned   # catch-all — must come last
        else:
            continue
        group_masks[gname] = mask
        group_sizes[gname] = int(mask.sum())
        assigned |= mask

    total_pop = sum(group_sizes.values()) or 1
    group_k = {
        gname: max(1, round(max_total_clusters * n / total_pop))
        for gname, n in group_sizes.items()
    }

    # ── Pass 2: cluster each group with its proportional k ───────────────────
    dna_rows = []
    for gname in groups:
        if gname not in group_masks:
            continue
        group_feat    = df_features[group_masks[gname]]
        group_profile = df_profile[df_profile['pidp'].isin(group_feat['pidp'])]

        if group_feat.empty:
            continue

        k       = group_k[gname]
        n       = len(group_feat)
        max_k   = min(k, max(1, n // min_cluster_size))
        chosen_k = best_k_by_silhouette(
            group_feat[feature_cols].values, max_k, min_silhouette
        )
        labels  = fit_kmeans(group_feat[feature_cols].values, chosen_k)

        group_feat = group_feat.copy()
        group_feat['_tribe_sub'] = labels

        for sub_id in sorted(group_feat['_tribe_sub'].unique()):
            sub_pidps = group_feat[group_feat['_tribe_sub'] == sub_id]['pidp']
            sub_prof  = group_profile[group_profile['pidp'].isin(sub_pidps)]
            label     = f"{gname} {sub_id + 1}" if chosen_k > 1 else gname
            dna_rows.append(build_dna_row(
                label, sub_prof, wave,
                summary_vars, variable_map, categorical_vars, category_maps,
                continuous_vars=continuous_vars,
            ))

    if not dna_rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(dna_rows)
        .sort_values('size', ascending=False)
        .reset_index(drop=True)
    )
