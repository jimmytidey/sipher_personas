# data_pipeline/config_variables_economic.py
#
# Economic variables: income, occupation, and migration/origin background.
# Same schema as config_variables.py. Omit UKHLS negative codes from ``recode`` (3a backfill → -1).
#
# Merged into config_variables.VARIABLES with other theme modules.

from __future__ import annotations

from typing import Any

VARIABLES: dict[str, dict[str, Any]] = {

    "fimngrs_dv": {
        "code":        "fimngrs_dv",
        "cluster":     False,
        "label":       "Total monthly personal income (Gross)",
        "categorical": False,
        "backfill":    None,
        "categories":  None,
        "one_hot":     None,
        "floor":       0,
        "clip":        8000,
    },
    "payn_dv": {
        "code":        "payn_dv",
        "cluster":     False,
        "label":       "Monthly net pay (take-home)",
        "categorical": False,
        "backfill":    None,
        "categories":  None,
        "one_hot":     None,
        "floor":       0,
        "clip":        8000,
    },

    "jbnssec8_dv": {
        "code":        "jbnssec8_dv",
        "cluster":     False,
        "label":       "Social Class (NS-SEC 8-class)",
        "categorical": False,
        "backfill":    None,
        "categories":  {
            -1.0: "Not provided",
            1.0: "Large employers & higher management",
            2.0: "Higher professional",
            3.0: "Lower management & professional",
            4.0: "Intermediate",
            5.0: "Small employers & own account",
            6.0: "Lower supervisory & technical",
            7.0: "Semi-routine",
            8.0: "Routine",
        },
        # UKHLS negative codes: not in recode — 3a backfill maps them to -1 (“not provided”).
        "group_labels": {
            -1.0: "Not provided",
            1.0: "Large employers & higher management",
            2.0: "Higher professional",
            3.0: "Lower management & professional",
            4.0: "Intermediate",
            5.0: "Small employers & own account",
            6.0: "Lower supervisory & technical",
            7.0: "Semi-routine",
            8.0: "Routine",
        },
        "one_hot":     None,
    },

    "bornuk_dv": {
        "code":        "bornuk_dv",
        "cluster":     False,
        "label":       "Born in UK",
        "categorical": True,
        "backfill":    ["xwavedat"],
        "categories":  {
            -1.0: "Not provided",
            1.0:  "Yes",
            2.0:  "No",
        },
        # UKHLS negative codes: not in recode — 3a backfill maps them to -1 (“not provided”).
        "one_hot": None,
    },

}

ECONOMIC_VARIABLES = VARIABLES
VARIABLE_MAP: dict[str, str] = {k: v["label"] for k, v in VARIABLES.items()}

__all__ = ["VARIABLES", "ECONOMIC_VARIABLES", "VARIABLE_MAP"]
