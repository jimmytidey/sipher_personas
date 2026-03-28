# data_pipeline/config_variables_local_service.py
#
# Housing tenure, neighbourhood cohesion, and ratings of local services (same schema
# as config_variables.py). See:
#   https://www.understandingsociety.ac.uk/documentation/mainstage/variables/tenure_dv/
#
# Each entry is a dict with:
#   code        - base variable name (wave prefix e.g. o_ handled by ingestion)
#   label       - human-readable description
#   categorical - True if categorical, False if continuous
#   categories  - dict mapping raw numeric code (float) -> English label, or None
#   group_labels- (optional) post-recode display labels
#   fill        - imputation: "mode" | "median" | "zero" | None | numeric
#   one_hot     - list of category codes to one-hot, or None / True
#   clip / floor- (optional) bounds for continuous variables
#   recode      - (optional) {raw_value -> new_value}
#   backfill    - list of codes triggering wave look-back, or None
#   bin_width   - (optional) fixed histogram bin width for visualisation
#   xwave       - (optional) True if sourced from xwavedat.pkl
#
# Merged into config_variables.VARIABLES with other theme modules (see config_variables.py).
#
# Notebooks often run with cwd=data_pipeline/ — use same-directory imports.

from __future__ import annotations

from typing import Any

# =============================================================================
# VARIABLES — single source of truth (read top-to-bottom in presentation order)
# =============================================================================

VARIABLES: dict[str, dict[str, Any]] = {

    # -------------------------------------------------------------------------
    # 1. Housing
    # -------------------------------------------------------------------------
    # UKHLS derived tenure (main survey); codes from variable documentation.
    "tenure_dv": {
        "code":        "tenure_dv",
        "label":       "Housing tenure (Own/Rent)",
        "categorical": True,
        "backfill":    None,
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            1.0: "Owned outright",
            2.0: "Owned with mortgage",
            3.0: "Local authority rent",
            4.0: "Housing association rented",
            5.0: "Rented from employer",
            6.0: "Rented private unfurnished",
            7.0: "Rented private furnished",
            8.0: "Other",
        },
        # Broad groups for display (optional downstream use)
        "recode": {
            -9.0: 0.0,
            -8.0: 0.0,
            1.0: 1.0,
            2.0: 1.0,
            3.0: 2.0,
            4.0: 2.0,
            5.0: 2.0,
            6.0: 2.0,
            7.0: 2.0,
            8.0: 3.0,
        },
        "group_labels": {
            0.0: "Not stated / inapplicable",
            1.0: "Owner-occupied",
            2.0: "Rented",
            3.0: "Other",
        },
        "fill":        "mode",
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 2. Neighbourhood
    # -------------------------------------------------------------------------
    "nbrsnci_dv": {
        "code":        "nbrsnci_dv",
        "label":       "Buckner Neighbourhood Cohesion Index",
        "categorical": True,
        "backfill":    [-9, -7, -2, -1],
        "categories":  None,
        "fill":        "median",
        "one_hot":     None,
        "bin_width":   1,
    },

    # -------------------------------------------------------------------------
    # 3. Local services (ordinal 1=Excellent … 5=Very poor)
    # -------------------------------------------------------------------------
    "locsera": {
        "code":        "locsera",
        "label":       "Standard of local services: Schools",
        "categorical": False,
        "backfill":    [-9, -7, -2, -1],
        "categories":  {
            1.0: "Excellent",
            2.0: "Good",
            3.0: "Fair",
            4.0: "Poor",
            5.0: "Very Poor/Bad",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "locserd": {
        "code":        "locserd",
        "label":       "Standard of local services: Shopping",
        "categorical": False,
        "backfill":    [-9, -7, -2, -1],
        "categories":  {
            1.0: "Excellent",
            2.0: "Good",
            3.0: "Fair",
            4.0: "Poor",
            5.0: "Very Poor/Bad",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "locsere": {
        "code":        "locsere",
        "label":       "Standard of local services: Leisure",
        "categorical": False,
        "backfill":    [-9, -7, -2, -1],
        "categories":  {
            1.0: "Excellent",
            2.0: "Good",
            3.0: "Fair",
            4.0: "Poor",
            5.0: "Very Poor/Bad",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
}

# -----------------------------------------------------------------------------
# Convenience exports (same pattern as config_variables_demographics.py)
# -----------------------------------------------------------------------------

LOCAL_SERVICE_VARIABLES = VARIABLES
LOCAL_SERVICE_ORDER: tuple[str, ...] = tuple(VARIABLES.keys())
VARIABLE_MAP: dict[str, str] = {k: v["label"] for k, v in VARIABLES.items()}

__all__ = [
    "VARIABLES",
    "LOCAL_SERVICE_ORDER",
    "LOCAL_SERVICE_VARIABLES",
    "VARIABLE_MAP",
]
