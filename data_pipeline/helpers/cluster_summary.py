"""
cluster_summary.py
------------------
Builds a pre-aggregated cluster summary DataFrame from a respondent-level
pipeline table.  Called by notebooks 8 and 9 to write the CSV that the API
serves from api/data/clusters/.
"""
from __future__ import annotations

import pandas as pd


_SEX_LABELS: dict[float, str] = {1.0: "Male", 2.0: "Female", -1.0: "Not provided"}

_CATEG_VARS = [
    "sex_dv", "jbstat", "racel_dv", "hiqual_dv",
    "marstat_dv", "tenure_dv", "hhtype_dv",
]
_CONTINU_VARS = [
    ("doby_dv", "age"),
    ("scsf1",   "health"),
]


def _label_maps_from_config() -> dict[str, dict[float, str]]:
    try:
        import data_pipeline.config_variables as cv  # noqa: PLC0415
        out: dict[str, dict[float, str]] = {}
        for base, vdef in cv.VARIABLES.items():
            src = vdef.get("categories") or vdef.get("group_labels") or {}
            out[base] = {float(k): str(v) for k, v in src.items()}
        return out
    except Exception:
        return {}


def make_cluster_summary(
    df: pd.DataFrame,
    cluster_col: str,
    wave: str = "k",
) -> pd.DataFrame:
    """
    Aggregate *df* by *cluster_col* and return a summary DataFrame with one row
    per cluster.

    Columns produced:
        cluster_id, tribe_label, size (SIPHER-weighted population), n_respondents
        age (mean), health (mean)
        <base>, <base>_pct  for each categorical variable in _CATEG_VARS
    """
    label_maps = _label_maps_from_config()
    rows: list[dict] = []

    for cluster_id, grp in df.groupby(cluster_col):
        size = int(grp["n_sipher_rows"].sum()) if "n_sipher_rows" in grp.columns else len(grp)
        rec: dict = {
            "cluster_id":    int(cluster_id),
            "tribe_label":   f"Cluster {int(cluster_id)}",
            "size":          size,
            "n_respondents": len(grp),
        }

        # Continuous means
        for base, out_key in _CONTINU_VARS:
            eng_col = f"{wave}_{base}_eng"
            raw_col = f"{wave}_{base}"
            col = eng_col if eng_col in grp.columns else (raw_col if raw_col in grp.columns else None)
            if col:
                vals = pd.to_numeric(grp[col], errors="coerce").dropna()
                if len(vals):
                    rec[out_key] = round(float(vals.mean()), 1)

        # Categorical modal value + percentage
        # Prefer raw numeric column (what the LLM was given) over _eng string labels.
        for base in _CATEG_VARS:
            eng_col = f"{wave}_{base}_eng"
            raw_col = f"{wave}_{base}"
            col = raw_col if raw_col in grp.columns else (eng_col if eng_col in grp.columns else None)
            if col is None:
                continue
            vals = pd.to_numeric(grp[col], errors="coerce").dropna()
            if len(vals) == 0:
                continue
            modes = vals.mode()
            if len(modes) == 0:
                continue
            mode_val = float(modes.iloc[0])
            mode_pct = round(int((vals == mode_val).sum()) / len(grp) * 100)
            if base == "sex_dv":
                label = _SEX_LABELS.get(mode_val, str(int(mode_val)))
            else:
                label = label_maps.get(base, {}).get(mode_val, str(int(mode_val)))
            rec[base]          = label
            rec[f"{base}_pct"] = mode_pct

            # Second-place value (stored when modal < 50%)
            remaining = vals[vals != mode_val]
            if mode_pct < 50 and len(remaining) > 0:
                modes2 = remaining.mode()
                if len(modes2) > 0:
                    val2 = float(modes2.iloc[0])
                    pct2 = round(int((vals == val2).sum()) / len(grp) * 100)
                    if base == "sex_dv":
                        label2 = _SEX_LABELS.get(val2, str(int(val2)))
                    else:
                        label2 = label_maps.get(base, {}).get(val2, str(int(val2)))
                    rec[f"{base}_2"]     = label2
                    rec[f"{base}_2_pct"] = pct2

        rows.append(rec)

    return pd.DataFrame(rows).sort_values("cluster_id").reset_index(drop=True)
