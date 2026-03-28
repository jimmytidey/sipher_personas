#!/usr/bin/env python3
"""Build xwave_response_rate.csv from xwave_description.csv + xwavedat.tab.

For each variable listed in xwave_description.csv, if a matching column exists in
xwavedat.tab, compute the percentage of rows where the value parses as a number
and is >= 0 (zero or positive). Non-numeric / NaN cells count as not satisfying.

Run from repo root:
  venv/bin/python data/0_raw/ukhls/build_xwave_response_rate.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DESC = HERE / "xwave_description.csv"
DAT = HERE / "xwavedat.tab"
OUT = HERE / "xwave_response_rate.csv"


def main() -> None:
    desc = pd.read_csv(DESC)
    df = pd.read_csv(DAT, sep="\t", low_memory=False)
    n_total = len(df)
    colnames = set(df.columns)

    out_rows = []
    for _, row in desc.iterrows():
        code = str(row["variable"]).strip()
        label = row.get("variable_label", "")
        if pd.isna(label):
            label = ""
        else:
            label = str(label)

        if code not in colnames:
            out_rows.append(
                {
                    "question_code": code,
                    "variable_label": label,
                    "pct_zero_or_positive": None,
                    "n_zero_or_positive": None,
                    "n_total_rows": int(n_total),
                    "in_xwavedat": False,
                }
            )
            continue

        s = pd.to_numeric(df[code], errors="coerce")
        n_ge0 = int((s >= 0).sum())
        pct = 100.0 * n_ge0 / n_total if n_total else float("nan")
        out_rows.append(
            {
                "question_code": code,
                "variable_label": label,
                "pct_zero_or_positive": round(pct, 2),
                "n_zero_or_positive": n_ge0,
                "n_total_rows": int(n_total),
                "in_xwavedat": True,
            }
        )

    out = pd.DataFrame(out_rows)
    out["n_zero_or_positive"] = out["n_zero_or_positive"].astype("Int64")
    out.to_csv(OUT, index=False)
    print(f"Wrote {OUT} ({len(out)} rows)")
    n_ok = int(out["in_xwavedat"].sum())
    print(f"Columns found in xwavedat.tab: {n_ok} / {len(out)}")


if __name__ == "__main__":
    main()
