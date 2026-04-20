# data_pipeline/config_variables_derived.py
#
# Composite variables produced in KEEP/5a_derive_variables.ipynb (not in raw UKHLS extracts).
# Merged into config_variables.VARIABLES for labels, maps, and downstream tools.

from __future__ import annotations

from typing import Any

VARIABLES: dict[str, dict[str, Any]] = {
    "digital_use": {
        "code":        "digital_use",
        "cluster":     False,
        "label":       "Composite digital engagement (0–1)",
        "categorical": False,
        "backfill":    None,
        "categories":  None,
        "one_hot":     None,
        "floor":       0,
        "clip":        1,
    },
    "service_use": {
        "code":        "service_use",
        "cluster":     False,
        "label":       "Composite health & benefit service use (0–1)",
        "categorical": False,
        "backfill":    None,
        "categories":  None,
        "one_hot":     None,
        "floor":       0,
        "clip":        1,
    },
    "derived_work_status": {
        "code":        "derived_work_status",
        "cluster":     False,
        "label":       "NS-SEC class (employed / self-employed only; else missing)",
        "categorical": False,
        "backfill":    None,
        "categories":  None,
        "one_hot":     None,
        "floor":       0,
        "clip":        8,
    },
}

DERIVED_VARIABLES = VARIABLES
DERIVED_ORDER: tuple[str, ...] = tuple(VARIABLES.keys())
VARIABLE_MAP: dict[str, str] = {k: v["label"] for k, v in VARIABLES.items()}

__all__ = [
    "VARIABLES",
    "DERIVED_ORDER",
    "DERIVED_VARIABLES",
    "VARIABLE_MAP",
]
