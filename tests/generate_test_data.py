#!/usr/bin/env python
# tests/generate_test_data.py
#
# Generates deterministic raw test data for the pipeline test harness.
# Run from the project root:
#
#     python tests/generate_test_data.py
#
# Output files (mirrors the real data/0_raw/ structure):
#
#   data_test/0_raw/admin_geography_mappings.csv
#   data_test/0_raw/sipher/sipher.csv
#   data_test/0_raw/ukhls/o_indresp.tab
#
# Design
# ------
# 100 respondents split across 2 synthetic LSOAs / 2 LAs.
# Each LA contains BOTH cluster types (25 each) so k=2 finds a clean split
# within every geography unit.
#
# All variable names mirror the real config_variables.py — no fake columns.
# The raw tab file contains every base variable in VARIABLE_MAP so the
# standard ingestion (notebook 2) can select columns as normal.
#
# Two cluster profiles (all Employed, jbstat raw=2, recoded to 1 in nb4):
#
#   Cluster A  → younger, high earner, degree-educated, good health
#     age_dv=25  hiqual_dv=1  payn_dv=3000  jbnssec8_dv=1  fimngrs_dv=3500
#     hhsize=4   nchild_dv=2  sf12mcs_dv=55  sf12pcs_dv=55
#     nbrsnci_dv=4  locsera/c/d/e=1  jbttwt=30  envhabit8=1
#     carmiles=5000  jbpl=1 (at home)  wktrvfar=1 (walk)  englang=1
#
#   Cluster B  → older, low earner, no quals, poor health
#     age_dv=65  hiqual_dv=5  payn_dv=0  jbnssec8_dv=8  fimngrs_dv=500
#     hhsize=1   nchild_dv=0  sf12mcs_dv=30  sf12pcs_dv=30
#     nbrsnci_dv=1  locsera/c/d/e=5  jbttwt=0  envhabit8=5
#     carmiles=0  jbpl=2 (employer premises)  wktrvfar=2 (car driver)  englang=2
#
# The clusters differ on many dimensions — k=2 KMeans separates them cleanly.

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_processing.config_variables import VARIABLE_MAP   # base codes only

RAW  = ROOT / "data_test" / "0_raw"

# ── Geography mapping ──────────────────────────────────────────────────────────
# step 5 reads: lsoa21cd, msoa21cd, msoa21nm, ladcd, ladnm
# synthetic_zone in sipher.csv is the lsoa21cd

GEO_ROWS = [
    {
        "lsoa21cd":  "E01TEST01",
        "msoa21cd":  "E02TEST01",
        "msoa21nm":  "Test MSOA A",
        "ladcd":     "E99000001",
        "ladnm":     "Test Borough A",
    },
    {
        "lsoa21cd":  "E01TEST02",
        "msoa21cd":  "E02TEST02",
        "msoa21nm":  "Test MSOA B",
        "ladcd":     "E99000002",
        "ladnm":     "Test Borough B",
    },
]

# ── Cluster profiles ───────────────────────────────────────────────────────────
# Raw values (before feature engineering) for each cluster profile.
# Keys are base variable codes (no wave prefix); wave prefix added in _make_row.

_A = {
    # Demographics
    "age_dv":       25.0,
    "sex_dv":       1.0,      # Male
    "englang":      1.0,      # Yes
    "oprlg1":       -8.0,     # Inapplicable
    # Socioeconomic
    "hiqual_dv":    1.0,      # Degree
    "payn_dv":      3000.0,
    "jbnssec8_dv":  1.0,
    "fimngrs_dv":   3500.0,
    # Household
    "hhsize":       4.0,
    "nchild_dv":    2.0,
    # Health
    "sf12mcs_dv":   55.0,
    "sf12pcs_dv":   55.0,
    # Community
    "nbrsnci_dv":   4.0,
    "locsera":      1.0,
    "locserc":      1.0,
    "locserd":      1.0,
    "locsere":      1.0,
    # Transport
    "jbttwt":       30.0,
    "envhabit8":    1.0,      # Always
    "carmiles":     5000.0,
    "caruse":       1.0,      # Has car
    "jbpl":         1.0,      # At home
    "wktrvfar":     1.0,      # Not drive (public transport)
    # Job
    "jbstat":       2.0,      # Paid employment (recoded to 1=Employed in notebook 4)
    "jlsic07_cc":   1.0,
    "socialkid":    1.0,
    # Disability (all absent)
    "alljbstat1":   1.0,
    "alljbstat3":   0.0,
    "alljbstat4":   0.0,
    "alljbstat5":   0.0,
    "alljbstat7":   0.0,
    "alljbstat8":   0.0,
}

_B = {
    "age_dv":       65.0,
    "sex_dv":       2.0,      # Female
    "englang":      2.0,      # No
    "oprlg1":       -8.0,
    "hiqual_dv":    5.0,      # Other/None
    "payn_dv":      0.0,
    "jbnssec8_dv":  8.0,
    "fimngrs_dv":   500.0,
    "hhsize":       1.0,
    "nchild_dv":    0.0,
    "sf12mcs_dv":   30.0,
    "sf12pcs_dv":   30.0,
    "nbrsnci_dv":   1.0,
    "locsera":      5.0,
    "locserc":      5.0,
    "locserd":      5.0,
    "locsere":      5.0,
    "jbttwt":       0.0,
    "envhabit8":    5.0,      # Never
    "carmiles":     0.0,
    "caruse":       2.0,      # No car
    "jbpl":         2.0,      # Employer premises
    "wktrvfar":     2.0,      # Drives
    "jbstat":       2.0,      # Paid employment (recoded to 1=Employed in notebook 4)
    "jlsic07_cc":   2.0,
    "socialkid":    2.0,
    "alljbstat1":   1.0,
    "alljbstat3":   0.0,
    "alljbstat4":   0.0,
    "alljbstat5":   0.0,
    "alljbstat7":   0.0,
    "alljbstat8":   0.0,
}

# Columns present in the real data but not in VARIABLE_MAP (needed as passthrough)
# These appear as raw UKHLS columns but are set to a safe default.
_EXTRA_DEFAULTS = {
    "disdif1":  -1.0,
    "disdif2":  -1.0,
    "disdif3":  -1.0,
    "disdif4":  -1.0,
    "disdif5":  -1.0,
    "disdif6":  -1.0,
    "disdif7":  -1.0,
    "disdif8":  -1.0,
    "disdif9":  -1.0,
    "disdif10": -1.0,
    "disdif11": -1.0,
    "disdif96": -1.0,
}

# All base codes we need to emit (everything in VARIABLE_MAP except pidp)
_ALL_BASES = [b for b in VARIABLE_MAP if b != "pidp"]

WAVE = "o"


def _is_cluster_a(pidp: int) -> bool:
    # Each LA block of 50 pidps is split 50/50:
    #   pidp  1–25  → zone E01TEST01, Cluster A
    #   pidp 26–50  → zone E01TEST01, Cluster B
    #   pidp 51–75  → zone E01TEST02, Cluster A
    #   pidp 76–100 → zone E01TEST02, Cluster B
    return pidp % 50 <= 25 and pidp % 50 != 0


def _zone(pidp: int) -> str:
    return "E01TEST01" if pidp <= 50 else "E01TEST02"


def _make_respondent(pidp: int) -> dict:
    profile = _A if _is_cluster_a(pidp) else _B
    row: dict = {"pidp": pidp}
    for base in _ALL_BASES:
        col = f"{WAVE}_{base}"
        if base in profile:
            row[col] = profile[base]
        elif base in _EXTRA_DEFAULTS:
            row[col] = _EXTRA_DEFAULTS[base]
        # derived/engineered variables (disability_*, alljbstat*) are not raw UKHLS columns — skip
    return row


RESPONDENTS = [_make_respondent(p) for p in range(1, 101)]

# ── SIPHER zone assignments ────────────────────────────────────────────────────

SIPHER_ROWS = [
    {"synthetic_zone": _zone(p), "pidp": p}
    for p in range(1, 101)
]


# ── Write files ────────────────────────────────────────────────────────────────

def write_csv(path: Path, rows: list[dict], delimiter: str = ",") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Written: {path.relative_to(ROOT)}  ({len(rows)} rows)")


if __name__ == "__main__":
    print("Generating test raw data (using real config_variables.py column names)...")

    write_csv(RAW / "admin_geography_mappings.csv", GEO_ROWS)
    write_csv(RAW / "sipher" / "sipher.csv",        SIPHER_ROWS)
    write_csv(RAW / "ukhls"  / "o_indresp.tab",     RESPONDENTS, delimiter="\t")

    print(f"\nDone. {len(RESPONDENTS[0]) - 1} columns per respondent.")
    print("Set USE_TEST_DATA = True in data_processing/config_paths.py, then run")
    print("notebooks 1 → 2 → 3 → 4 → 5 → 6 to generate data_test/6_cluster/LA_clusters.csv")
