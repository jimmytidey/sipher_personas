#!/usr/bin/env python3
"""Collapse numbered variants: keep first row per stem (strip trailing digits from variable_id).

Reads metadata/ukhls/n_indresp_main_waves_nonneg_pct_no_health.csv in order; for any group of
variable names that differ only by a suffix of digits (e.g. n_respchild1 … n_respchild16),
keeps the first occurrence and drops the rest.

Writes metadata/ukhls/n_indresp_main_waves_nonneg_pct_no_health_short.csv

Usage (from repo root):
  venv/bin/python metadata/ukhls/shorten_indresp_nonneg_no_health.py
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "metadata" / "ukhls" / "n_indresp_main_waves_nonneg_pct_no_health.csv"
OUT = REPO / "metadata" / "ukhls" / "n_indresp_main_waves_nonneg_pct_no_health_short.csv"

_TRAILING_DIGITS = re.compile(r"\d+$")


def _stem(variable_id: str) -> str:
    return _TRAILING_DIGITS.sub("", str(variable_id).strip())


def main() -> None:
    df = pd.read_csv(SRC)
    n_before = len(df)
    df = df.assign(_stem=df["variable_id"].map(_stem))
    df = df.drop_duplicates(subset="_stem", keep="first").drop(columns=["_stem"])
    df.to_csv(OUT, index=False)
    print(f"Wrote {OUT} ({len(df)} rows, removed {n_before - len(df)} numbered duplicates)")


if __name__ == "__main__":
    main()
