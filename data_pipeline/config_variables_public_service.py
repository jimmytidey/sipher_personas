# data_pipeline/config_variables_public_service.py
#
# GP / hospital / advice service use, benefit receipts, and total social benefit income
# (same schema as config_variables.py). hl2gp / servuse* mirror config_variables_llm_generated;
# benefit flags follow UKDA value labels (not mentioned / mentioned).
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
    # 1. Service use (health & advice)
    # -------------------------------------------------------------------------
    "hl2gp": {
        "code":        "hl2gp",
        "label":       "Visited GP in last 12 months",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            0.0: "None",
            1.0: "One or two",
            2.0: "Three to five",
            3.0: "Six to ten",
            4.0: "More than ten",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "servuse2": {
        "code":        "servuse2",
        "label":       "Service use (12m): local hospital",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            0.0: "Not mentioned",
            1.0: "Mentioned",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "servuse10": {
        "code":        "servuse10",
        "label":       "Use of advice services (benefits/debt/legal)",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            0.0: "Not mentioned",
            1.0: "Mentioned",
        },
        "fill":        "mode",
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 2. Benefit receipts (mentioned / not mentioned)
    # -------------------------------------------------------------------------
    "benbase4": {
        "code":        "benbase4",
        "label":       "Receipt: Universal Credit",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            0.0: "Not mentioned",
            1.0: "Mentioned",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "othben6": {
        "code":        "othben6",
        "label":       "Receipt: Council Tax Reduction",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            0.0: "Not mentioned",
            1.0: "Mentioned",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "othben8": {
        "code":        "othben8",
        "label":       "Receipt: Housing Benefit",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            0.0: "Not mentioned",
            1.0: "Mentioned",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "othben1": {
        "code":        "othben1",
        "label":       "Receipt: Foster Allowance",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            0.0: "Not mentioned",
            1.0: "Mentioned",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "othben2": {
        "code":        "othben2",
        "label":       "Receipt: Maternity Allowance",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            0.0: "Not mentioned",
            1.0: "Mentioned",
        },
        "fill":        "mode",
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 3. Income — administrative total (UKDA: amount income component 7)
    # -------------------------------------------------------------------------
    "fimnsben_dv": {
        "code":        "fimnsben_dv",
        "label":       "Social benefit income amount (total)",
        "categorical": False,
        "backfill":    [-9, -8, -2, -1],
        "categories":  None,
        "fill":        0.0,
        "one_hot":     None,
        "floor":       0,
        "clip":        15000,
    },
}

# -----------------------------------------------------------------------------
# Convenience exports (same pattern as config_variables_demographics.py)
# -----------------------------------------------------------------------------

PUBLIC_SERVICE_VARIABLES = VARIABLES
PUBLIC_SERVICE_ORDER: tuple[str, ...] = tuple(VARIABLES.keys())
VARIABLE_MAP: dict[str, str] = {k: v["label"] for k, v in VARIABLES.items()}

__all__ = [
    "VARIABLES",
    "PUBLIC_SERVICE_ORDER",
    "PUBLIC_SERVICE_VARIABLES",
    "VARIABLE_MAP",
]
