#!/usr/bin/env python3
"""Drop health-related variables from a nonnegative-% CSV (same columns as the build output).

Default input/output is the full-table filter to n_indresp_main_waves_nonneg_pct_no_health.csv.
Use --input/--output to filter other files (e.g. the _short subset).

Removes rows that match either:
- variable_id stems used for UKHLS health / disability / conditions / service use / wellbeing /
  smoking / alcohol / covid modules (with a short false-positive allowlist), or
- description text matching health-related phrases (regex list).

Usage (from repo root):
  venv/bin/python metadata/ukhls/filter_indresp_nonneg_no_health.py
  venv/bin/python metadata/ukhls/filter_indresp_nonneg_no_health.py \\
    --input metadata/ukhls/n_indresp_main_waves_nonneg_pct_no_health_short.csv \\
    --output metadata/ukhls/n_indresp_main_waves_nonneg_pct_no_health_short.csv
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DEFAULT_SRC = REPO / "metadata" / "ukhls" / "n_indresp_main_waves_nonneg_pct.csv"
DEFAULT_OUT = REPO / "metadata" / "ukhls" / "n_indresp_main_waves_nonneg_pct_no_health.csv"

# Never treat as health despite substrings (e.g. hidp ~ "hid" is not hcond).
_ID_ALLOWLIST = frozenset(
    {
        "n_hidp",
        "n_hhorig",
        "n_hhorig2",
        "n_hhorig3",
    }
)

# Longest-first stems so hcondcode matches before hcond.
_ID_HEALTH_STEMS: tuple[str, ...] = (
    "hcondcode",
    "hconda",
    "hconds",
    "hcondn",
    "hcondp",
    "hcondnew",
    "prevhcond",
    "disdif",
    "dissev",
    "mhcond",
    "hcond",
    "hosp",
    "hl2",
    "sf12",
    "scghq",
    "jwbs",
    "smever",
    "smnow",
    "ncigs",
    "longcov",
    "testposcov",
    "lgcv",
    "hlth",
    "pregsmoke",
    "auditc",
    "aedrof",
    "aepuwk",
    "aepuda",
    "mhgad",
    "pregfert",
    "brfed",
    "illwk",
)

_DESC_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bhealth\b",
        r"\bhospital\b",
        r"\bdisabilit",
        r"\bimpairment\b",
        r"diagnosed health",
        r"mental health",
        r"\bsf-12\b",
        r"ghq",
        r"job-related well",
        r"well-being scale",
        r"wellbeing",
        r"well-being",
        r"\bsmoking\b",
        r"\bsmoked\b",
        r"cigarette",
        r"\bcovid\b",
        r"vaccin",
        r"long cov",
        r"\bdiabetes\b",
        r"\basthma\b",
        r"\bcancer\b",
        r"\bstroke\b",
        r"\barthritis\b",
        r"high blood pressure",
        r"epilepsy",
        r"fruit and vegetables",
        r"five a day",
        r"admitted to hospital",
        r"health condition",
        r"long-standing",
        r"limiting long-standing",
        r"psychological",
        r"distress",
        r"anxiety",
        r"depression",
        r"alcohol consumption",
        r"units of alcohol",
        r"days drank alcohol",
        r"\balcohol\b",
        r"\bheight\b",
        r"\bweight\b",
        r"\bbmi\b",
        r"waist",
        r"prescription",
        r"medication",
        r"pill",
        r"contracept",
        r"nurse",
        r"consultation",
        r"outpatient",
        r"\bgp visits\b",
        r"how much difficulty do you have",
        r"\bphobia\b",
        r"panic attacks",
        r"mental health condition",
        r"fertility treatment",
        r"breastfeed",
        r"breastfeeding",
        r"\bgad\b",
        r"generalised anxiety",
        r"generalized anxiety",
        r"work illness",
        r"eyesight problems",
    )
)


def _is_health_variable_id(vid: str) -> bool:
    v = str(vid).lower().strip()
    if v in _ID_ALLOWLIST:
        return False
    if not v.startswith("n_"):
        return False
    base = v[2:]
    return any(base.startswith(st) for st in _ID_HEALTH_STEMS)


def _is_health_description(desc: object) -> bool:
    if desc is None or (isinstance(desc, float) and pd.isna(desc)):
        return False
    t = str(desc)
    return any(p.search(t) for p in _DESC_PATTERNS)


def main() -> None:
    ap = argparse.ArgumentParser(description="Remove health-related rows from nonnegative-% CSV.")
    ap.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_SRC,
        help=f"Input CSV (default: {DEFAULT_SRC.relative_to(REPO)})",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output CSV (default: {DEFAULT_OUT.relative_to(REPO)})",
    )
    args = ap.parse_args()
    src = args.input if args.input.is_absolute() else REPO / args.input
    out = args.output if args.output.is_absolute() else REPO / args.output

    df = pd.read_csv(src)
    drop = df["variable_id"].map(_is_health_variable_id) | df["description"].map(
        _is_health_description
    )
    filtered = df[~drop].copy()
    filtered.to_csv(out, index=False)
    print(f"Wrote {out} ({len(filtered)} rows, dropped {drop.sum()} from {len(df)})")


if __name__ == "__main__":
    main()
