# data_pipeline/config_variables_digital.py
#
# Internet / mobile-technology use (UKHLS indresp, wave-prefixed columns e.g. o_netpusenew).
# Same schema as config_variables.py.
#
# Merged into config_variables.VARIABLES (see config_variables.py).

from __future__ import annotations

from typing import Any

# UKHLS 1–6 frequency scale (mobile tech module — browsing, email, social, etc.)
_FREQ_INTERNET_ACTIVITY: dict[float, str] = {
    -1.0: "Not provided",
    1.0: "Every day",
    2.0: "Several times a week",
    3.0: "Several times a month",
    4.0: "Once a month",
    5.0: "Less than once a month",
    6.0: "Never",
}

_YES_NO: dict[float, str] = {
    -1.0: "Not provided",
    1.0: "Yes",
    2.0: "No",
}

VARIABLES: dict[str, dict[str, Any]] = {

    "netpusenew": {
        "code":        "netpusenew",
        "cluster":     False,
        "label":       "Internet use frequency",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -1.0: "Not provided",
            1.0: "Almost all of the time",
            2.0: "Several times a day",
            3.0: "Once or twice a day",
            4.0: "Several times a week",
            5.0: "Several times a month",
            6.0: "Once a month",
            7.0: "Less than once a month",
            8.0: "Never use",
            9.0: "No access at home, at work or elsewhere",
        },
        "one_hot":     None,
    },
    "laptop": {
        "code":        "laptop",
        "cluster":     False,
        "label":       "Access to a laptop",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_YES_NO),
        "one_hot":     None,
    },
    "smtphone": {
        "code":        "smtphone",
        "cluster":     False,
        "label":       "Has / Access to a smartphone",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_YES_NO),
        "one_hot":     None,
    },
    "browse": {
        "code":        "browse",
        "cluster":     False,
        "label":       "Frequency: Browsing websites",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_INTERNET_ACTIVITY),
        "one_hot":     None,
    },
    "email": {
        "code":        "email",
        "cluster":     False,
        "label":       "Frequency: Email",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_INTERNET_ACTIVITY),
        "one_hot":     None,
    },
    "smlook": {
        "code":        "smlook",
        "cluster":     False,
        "label":       "Frequency: Looking at Social Media",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_INTERNET_ACTIVITY),
        "one_hot":     None,
    },
    "smpost": {
        "code":        "smpost",
        "cluster":     False,
        "label":       "Frequency: Posting on Social Media",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_INTERNET_ACTIVITY),
        "one_hot":     None,
    },
    "onlinebuy": {
        "code":        "onlinebuy",
        "cluster":     False,
        "label":       "Frequency: Online buying",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_INTERNET_ACTIVITY),
        "one_hot":     None,
    },
    "onlinebank": {
        "code":        "onlinebank",
        "cluster":     False,
        "label":       "Frequency: Online banking",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_INTERNET_ACTIVITY),
        "one_hot":     None,
    },
    "streaming": {
        "code":        "streaming",
        "cluster":     False,
        "label":       "Frequency: Streaming videos",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_INTERNET_ACTIVITY),
        "one_hot":     None,
    },
}

DIGITAL_VARIABLES = VARIABLES
DIGITAL_ORDER: tuple[str, ...] = tuple(VARIABLES.keys())
VARIABLE_MAP: dict[str, str] = {k: v["label"] for k, v in VARIABLES.items()}

__all__ = [
    "VARIABLES",
    "DIGITAL_ORDER",
    "DIGITAL_VARIABLES",
    "VARIABLE_MAP",
]
