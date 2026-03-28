#!/usr/bin/env python3
"""Merge xwave_description.csv with % of values >= 0 from xwavedat.tab.

- pct_ge_0_all_rows: 100 * count(value >= 0) / n_rows (NaN counts as not >= 0)
- pct_ge_0_of_numeric: among non-null numeric values only, % that are >= 0

Requires: pandas. Run from repo root: python data/0_raw/ukhls/compute_xwave_ge0_pct.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DESC = HERE / "xwave_description.csv"
DAT = HERE / "xwavedat.tab"
OUT = HERE / "xwave_description_ge0_pct.csv"


def main() -> None:
    desc = pd.read_csv(DESC)
    df = pd.read_csv(DAT, sep="\t", low_memory=False)
    n = len(df)
    cols = set(df.columns)

    rows = []
    for _, r in desc.iterrows():
        var = str(r["variable"]).strip()
        if var not in cols:
            rows.append(
                {
                    "pct_ge_0_all_rows": None,
                    "pct_ge_0_of_numeric": None,
                    "n_ge_0": None,
                    "n_numeric": None,
                    "n_rows": n,
                    "in_xwavedat": False,
                }
            )
            continue
        s = pd.to_numeric(df[var], errors="coerce")
        nn = int(s.notna().sum())
        n_ge0 = int((s >= 0).sum())
        pct_all = 100.0 * n_ge0 / n if n else float("nan")
        pct_num = 100.0 * (s >= 0).sum() / nn if nn else float("nan")
        rows.append(
            {
                "pct_ge_0_all_rows": round(pct_all, 2),
                "pct_ge_0_of_numeric": round(float(pct_num), 2),
                "n_ge_0": n_ge0,
                "n_numeric": nn,
                "n_rows": n,
                "in_xwavedat": True,
            }
        )

    out = pd.concat([desc.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    out.to_csv(OUT, index=False)
    print(f"Wrote {OUT} ({len(out)} rows)")
    miss = out.loc[~out["in_xwavedat"], "variable"].tolist()
    print(f"Variables in description but not in xwavedat.tab: {len(miss)}")


if __name__ == "__main__":
    main()
