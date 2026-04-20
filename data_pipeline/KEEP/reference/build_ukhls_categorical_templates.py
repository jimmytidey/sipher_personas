#!/usr/bin/env python3
"""
Regenerate empty UKHLS categorical reference CSVs from config_variables.py.

One file per categorical variable:  ukhls_categorical/<variable_code>.csv

Run from repo root:
  python data_pipeline/reference/build_ukhls_categorical_templates.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from data_pipeline.config_variables import VARIABLES  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "ukhls_categorical"
HEADER = ["category_code", "label", "percent", "n"]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n_files = 0
    for code, spec in sorted(VARIABLES.items()):
        if not spec.get("categorical"):
            continue
        cat_map = spec.get("group_labels") or spec.get("categories")
        if not cat_map:
            continue
        path = OUT_DIR / f"{code}.csv"
        rows = []
        for k in sorted(cat_map.keys(), key=lambda x: (isinstance(x, float), x)):
            label = cat_map[k]
            rows.append(
                {
                    "category_code": k,
                    "label": label,
                    "percent": "",
                    "n": "",
                }
            )
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=HEADER)
            w.writeheader()
            w.writerows(rows)
        n_files += 1
        print(path.name, len(rows), "categories")

    print(f"\nWrote {n_files} CSVs to {OUT_DIR}")


if __name__ == "__main__":
    main()
