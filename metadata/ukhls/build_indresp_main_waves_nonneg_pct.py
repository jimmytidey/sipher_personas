#!/usr/bin/env python3
"""Build CSV: variable id, description from n_indresp_question_text_report.txt, pooled % nonnegative.

Reads all {wave}_indresp.tab files under data/0_raw/ukhls (not pickles). For each variable
listed in the report, maps wave-specific columns (e.g. b_hidp, n_hidp) to a base name (hidp)
and pools counts across main waves.

Usage (from repo root):
  venv/bin/python metadata/ukhls/build_indresp_main_waves_nonneg_pct.py

Outputs:
  metadata/ukhls/n_indresp_main_waves_nonneg_pct.csv
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
REPORT_PATH = REPO / "metadata" / "ukhls" / "n_indresp_question_text_report.txt"
RAW_DIR = REPO / "data" / "0_raw" / "ukhls"
OUT_PATH = REPO / "metadata" / "ukhls" / "n_indresp_main_waves_nonneg_pct.csv"

# UKHLS main stage waves (b–o). Wave `a` is BHPS-only; `f` is not released. Omit `a` unless needed.
MAIN_WAVE_LETTERS = "bcdefghijklmno"

# Single-letter wave prefix + underscore, e.g. b_hidp -> hidp; pidp unchanged.
_WAVE_PREFIX_RE = re.compile(r"^[a-z]_(.+)$")

CHUNKSIZE = 50_000


def _base_from_column(name: str) -> str:
    m = _WAVE_PREFIX_RE.match(name.strip())
    return m.group(1) if m else name.strip()


def _report_var_to_base(report_var: str) -> str:
    return _base_from_column(report_var)


def parse_report(path: Path) -> list[tuple[str, str]]:
    """Return [(variable_id, description), ...] from tab-separated body after header row."""
    rows: list[tuple[str, str]] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("variable\t") or line.startswith("variable "):
                break
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("\t", 1)
            if len(parts) < 2:
                continue
            vid, desc = parts[0].strip(), parts[1].strip()
            if vid:
                rows.append((vid, desc))
    return rows


def discover_indresp_tabs(raw_dir: Path) -> list[Path]:
    paths = []
    for w in MAIN_WAVE_LETTERS:
        p = raw_dir / f"{w}_indresp.tab"
        if p.is_file():
            paths.append(p)
    return paths


def main() -> None:
    report_rows = parse_report(REPORT_PATH)
    if not report_rows:
        raise SystemExit(f"No variables parsed from {REPORT_PATH}")

    # variable_id (as in report) -> base name
    vid_to_base = {vid: _report_var_to_base(vid) for vid, _ in report_rows}
    base_to_vid = {}
    for vid, b in vid_to_base.items():
        base_to_vid.setdefault(b, vid)

    bases_needed = set(vid_to_base.values())

    tab_paths = discover_indresp_tabs(RAW_DIR)
    if not tab_paths:
        raise SystemExit(f"No *_indresp.tab under {RAW_DIR}")

    # Pooled counts per base name
    total_by_base: dict[str, int] = {b: 0 for b in bases_needed}
    nonneg_by_base: dict[str, int] = {b: 0 for b in bases_needed}

    for tab_path in tab_paths:
        # Map column name -> base for columns we care about
        header = pd.read_csv(tab_path, sep="\t", nrows=0).columns.tolist()
        col_to_base: dict[str, str] = {}
        for c in header:
            b = _base_from_column(c)
            if b in bases_needed:
                col_to_base[c] = b

        if not col_to_base:
            continue

        usecols = list(col_to_base.keys())
        for chunk in pd.read_csv(
            tab_path,
            sep="\t",
            usecols=usecols,
            chunksize=CHUNKSIZE,
            low_memory=False,
        ):
            for col, base in col_to_base.items():
                s = pd.to_numeric(chunk[col], errors="coerce")
                n = len(s)
                total_by_base[base] += n
                nonneg_by_base[base] += int((s >= 0).sum())

    out_rows: list[dict] = []
    for vid, desc in report_rows:
        b = vid_to_base[vid]
        t = total_by_base.get(b, 0)
        nn = nonneg_by_base.get(b, 0)
        pct = round(100.0 * nn / t, 4) if t else None
        out_rows.append(
            {
                "variable_id": vid,
                "description": desc,
                "pct_nonnegative": pct,
            }
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["variable_id", "description", "pct_nonnegative"],
        )
        w.writeheader()
        w.writerows(out_rows)

    print(f"Wrote {OUT_PATH} ({len(out_rows)} rows)")
    print(f"Wave files used: {[p.name for p in tab_paths]}")


if __name__ == "__main__":
    main()
