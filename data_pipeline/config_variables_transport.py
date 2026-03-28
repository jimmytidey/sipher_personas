# data_pipeline/config_variables_transport.py
#
# Public transport ratings, travel frequencies, car ownership, commuting, and transport
# barriers (same schema as config_variables.py).
#
# UKHLS base names are used as dict keys so step-2 ingestion finds o_<code> columns.
# Mappings from your short names:
#   • "caruse" (frequency)  → trcarfq   (binary car access is caruse — not in this module)
#   • "bususe" / "trainuse" / "cycleuse" / "walkuse" → trbusfq, trtrnfq, trbikefq, walkfreq
#   • "hw_uk" (UK licence)  → drive      (no hw_uk in standard indresp; drive = has licence)
#
# Value labels for 1–9 travel frequencies follow UKDA (n_trbusfq etc.).
#
# Notebooks often run with cwd=data_pipeline/ — use same-directory imports.

from __future__ import annotations

from typing import Any

# ── Shared: UKHLS 1–9 frequency scale (travel by mode) — UKDA n_trbusfq et al. ─────────
_FREQ_TRAVEL_CATEGORIES: dict[float, str] = {
    -9.0: "Missing",
    -8.0: "Inapplicable",
    -7.0: "Proxy",
    -2.0: "Refusal",
    -1.0: "Don't know",
    1.0: "At least once a day",
    2.0: "5 or more times a week, but not every day",
    3.0: "3 or 4 times a week",
    4.0: "Once or twice a week",
    5.0: "Less than that but more than twice a month",
    6.0: "Once or twice a month",
    7.0: "Less than that but more than twice a year",
    8.0: "Once or twice a year",
    9.0: "Less than that or never",
}

# =============================================================================
# VARIABLES — single source of truth (read top-to-bottom in presentation order)
# =============================================================================

VARIABLES: dict[str, dict[str, Any]] = {

    # -------------------------------------------------------------------------
    # 1. Local area — public transport quality & access
    # -------------------------------------------------------------------------
    "locserc": {
        "code":        "locserc",
        "label":       "Standard of local services: Public transport",
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
    # Ease of access to PT — same 1–5 ordinal as other “local services” items when field is present
    "traccess": {
        "code":        "traccess",
        "label":       "Ease of access to public transport",
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

    # -------------------------------------------------------------------------
    # 2. Frequency of travel by mode (1–9 scale)
    # -------------------------------------------------------------------------
    "trcarfq": {
        "code":        "trcarfq",
        "label":       "Frequency of car use",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_TRAVEL_CATEGORIES),
        "fill":        "mode",
        "one_hot":     None,
    },
    "trbusfq": {
        "code":        "trbusfq",
        "label":       "Frequency of bus use",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_TRAVEL_CATEGORIES),
        "fill":        "mode",
        "one_hot":     None,
    },
    "trtrnfq": {
        "code":        "trtrnfq",
        "label":       "Frequency of train/metro use",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_TRAVEL_CATEGORIES),
        "fill":        "mode",
        "one_hot":     None,
    },
    "trbikefq": {
        "code":        "trbikefq",
        "label":       "Frequency of cycling",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_TRAVEL_CATEGORIES),
        "fill":        "mode",
        "one_hot":     None,
    },
    "walkfreq": {
        "code":        "walkfreq",
        "label":       "Frequency of walking (15min+)",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  dict(_FREQ_TRAVEL_CATEGORIES),
        "fill":        "mode",
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 3. Household vehicles (often hhresp; keys kept for harmonised extracts)
    # -------------------------------------------------------------------------
    "pcarown": {
        "code":        "pcarown",
        "label":       "Household has access to a car/van",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            1.0: "Yes",
            2.0: "No",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "ncars": {
        "code":        "ncars",
        "label":       "Number of cars in household",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  None,
        "fill":        0.0,
        "one_hot":     None,
        "floor":       0,
        "clip":        20,
    },
    "carmiles": {
        "code":        "carmiles",
        "label":       "Miles driven in last 12 months",
        "categorical": False,
        "backfill":    None,
        "categories":  None,
        "fill":        "zero",
        "one_hot":     None,
        "floor":       0,
        "clip":        50_000,
    },

    # -------------------------------------------------------------------------
    # 4. Licence & transport-related strain / barriers (ordinal 1–5 unless noted)
    # -------------------------------------------------------------------------
    "drive": {
        "code":        "drive",
        "label":       "Holds a valid UK driving license",
        "categorical": True,
        "backfill":    [-9, -8, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -2.0: "Refusal",
            -1.0: "Don't know",
            1.0: "Yes",
            2.0: "No",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "trcost": {
        "code":        "trcost",
        "label":       "Concern over transport costs",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            1.0: "Not at all",
            2.0: "Slightly",
            3.0: "Moderately",
            4.0: "Quite a bit",
            5.0: "Very much",
        },
        "fill":        "median",
        "one_hot":     None,
    },
    "fuelcost": {
        "code":        "fuelcost",
        "label":       "Difficulty meeting vehicle running costs",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            1.0: "Not at all",
            2.0: "Slightly",
            3.0: "Moderately",
            4.0: "Quite a bit",
            5.0: "Very much",
        },
        "fill":        "median",
        "one_hot":     None,
    },
    "transp_diff": {
        "code":        "transp_diff",
        "label":       "Difficulty getting to places (transport reasons)",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            1.0: "Not at all",
            2.0: "Slightly",
            3.0: "Moderately",
            4.0: "Quite a bit",
            5.0: "Very much",
        },
        "fill":        "median",
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 5. Commuting (from config_variables.py)
    # -------------------------------------------------------------------------
    "jbttwt": {
        "code":        "jbttwt",
        "label":       "Minutes spent travelling to work",
        "categorical": False,
        "backfill":    [-9, -7, -2, -1],
        "categories":  None,
        "fill":        "zero",
        "one_hot":     None,
        "clip":        120,
    },
    "wktrvfar": {
        "code":        "wktrvfar",
        "label":       "Main mode of transport to work",
        "categorical": True,
        "backfill":    None,
        "categories":  {
            -8.0: "Inapplicable",
            -1.0: "Missing / not stated",
            1.0: "Drive myself by car or van",
            2.0: "Get a lift with someone from household",
            3.0: "Get a lift with someone outside the household",
            4.0: "Motorcycle/moped/scooter",
            5.0: "Taxi/minicab",
            6.0: "Bus/coach",
            7.0: "Train",
            8.0: "Underground/Metro/Tram/Light railway",
            9.0: "Cycle",
            10.0: "Walk",
            97.0: "Other",
        },
        "fill":        "mode",
        "one_hot":     [1.0],
        "group_labels": {1.0: "Drives to work"},
    },
}

# -----------------------------------------------------------------------------
# Convenience exports (same pattern as config_variables_demographics.py)
# -----------------------------------------------------------------------------

TRANSPORT_VARIABLES = VARIABLES
TRANSPORT_ORDER: tuple[str, ...] = tuple(VARIABLES.keys())
VARIABLE_MAP: dict[str, str] = {k: v["label"] for k, v in VARIABLES.items()}

__all__ = [
    "VARIABLES",
    "TRANSPORT_ORDER",
    "TRANSPORT_VARIABLES",
    "VARIABLE_MAP",
]
