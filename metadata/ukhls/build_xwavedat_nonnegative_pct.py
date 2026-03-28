#!/usr/bin/env python3
"""For every column in xwavedat.pkl, compute % of rows with numeric value >= 0.

Non-numeric cells (after coercion) count as not non-negative.

Run: venv/bin/python data/0_raw/ukhls/build_xwavedat_nonnegative_pct.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# .../data/0_raw/ukhls/this_script.py -> repo root is parents[3]
REPO = Path(__file__).resolve().parents[3]
PKL = REPO / "data" / "2_pickle_ukhls_waves" / "xwavedat.pkl"
OUT = REPO / "data" / "0_raw" / "ukhls" / "xwavedat_nonnegative_pct.csv"


def main() -> None:
    df = pd.read_pickle(PKL)
    n = len(df)
    rows = []
    for col in df.columns:
        s = pd.to_numeric(df[col], errors="coerce")
        n_nn = int(s.notna().sum())
        n_ge0 = int((s >= 0).sum())
        pct = 100.0 * n_ge0 / n if n else float("nan")
        rows.append(
            {
                "variable": col,
                "pct_nonnegative": round(pct, 4),
                "n_nonnegative": n_ge0,
                "n_numeric": n_nn,
                "n_rows": int(n),
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"Wrote {OUT} ({len(out)} variables, {n} rows)")


if __name__ == "__main__":
    main()
