# data_pipeline/config_variables_sipher_weighted.py
#
# Curated demographic + selected health variables (same schema as config_variables.py).
# Each entry is a dict with:
#   code        - base variable name (wave prefix e.g. o_ handled by ingestion)
#   label       - human-readable description
#   categorical - True if categorical, False if continuous
#   categories  - dict mapping raw numeric code (float) -> English label, or None
#   group_labels- (optional) post-recode display labels {canonical_code -> label}
#   one_hot     - list of category codes to one-hot, or None / True
#   clip / floor- (optional) bounds for continuous variables
#   recode      - (optional) {raw_value -> new_value} (omit UKHLS negatives — 3a backfill → -1)
#   backfill    - list of codes triggering wave look-back, or None
#   file        - (optional) source file: "xwave" for xwavedat.pkl, "hhresp" for
#                 household response; omit (or "indresp") for individual response
#   transform   - (optional) e.g. "birth_year_to_age"
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
    # 1. Demographics
    # -------------------------------------------------------------------------
    "doby_dv": {
        "code":        "doby_dv",
        "cluster":     True,
        "label":       "Age",
        "categorical": False,
        "categories":  None,
        "one_hot":     None,
        "backfill":    None,
        "file":        "xwave",
        "transform":   "birth_year_to_age",
    },
    "sex_dv": {
        "code":        "sex_dv",
        "cluster":     True,
        "label":       "Sex (Derived)",
        "categorical": True,
        "backfill":    None,
        "categories":  {
            -1.0: "Not provided",
            0.0: "Inconsistent",
            1.0: "Male",
            2.0: "Female",
        },
        "one_hot":     None,
        "file":        "xwave",
    },
    # xwavedat: UKHLS racel_dv — used for CLUSTER_VARS
    "racel_dv": {
        "code":        "racel_dv",
        "cluster":     True,
        "label":       "Ethnic group",
        "file":        "xwave",
        "categorical": True,
        "backfill":    None,
        "categories":  {
            -1.0: "Not provided",
             1.0: "White: British/English/Scottish/Welsh/N. Irish",
             2.0: "White: Irish",
             3.0: "Gypsy or Irish traveller",
             4.0: "White: Other",
             5.0: "Mixed: White and Black Caribbean",
             6.0: "Mixed: White and Black African",
             7.0: "Mixed: White and Asian",
             8.0: "Mixed: Other",
             9.0: "Asian: Indian",
            10.0: "Asian: Pakistani",
            11.0: "Asian: Bangladeshi",
            12.0: "Asian: Chinese",
            13.0: "Asian: Other",
            14.0: "Black: Caribbean",
            15.0: "Black: African",
            16.0: "Black: Other",
            17.0: "Arab",
            97.0: "Other ethnic group",
        },
        # UKHLS negative codes: not in recode — 3a backfill maps them to -1 (“not provided”).
        "recode": {
             1.0:  1.0,
             2.0:  1.0,
             3.0:  1.0,
             4.0:  1.0,
             5.0:  2.0,
             6.0:  2.0,
             7.0:  2.0,
             8.0:  2.0,
             9.0:  3.0,
            10.0:  4.0,
            11.0:  4.0,
            12.0:  5.0,
            13.0:  5.0,
            17.0:  6.0,
            14.0:  7.0,
            15.0:  8.0,
            16.0:  8.0,
            97.0:  9.0,
        },
        "group_labels": {
            -1.0: "Not provided",
            1.0: "White",
            2.0: "Mixed",
            3.0: "Indian",
            4.0: "Pakistani / Bangladeshi",
            5.0: "Other Asian",
            6.0: "Arab",
            7.0: "Caribbean",
            8.0: "African",
            9.0: "Other",
        },
        "one_hot": True,
    },
    "hiqual_dv": {
        "code":        "hiqual_dv",
        "cluster":     True,
        "label":       "Highest qualification",
        "categorical": False,
        "backfill":    [-9, -8, -2, -1],
        "categories":  {
            -1.0: "Not provided",
            1.0: "Degree",       2.0: "Other higher degree",
            3.0: "A-level etc",  4.0: "GCSE etc",
            5.0: "Other qualification", 9.0: "No qualification",
        },
        "one_hot":     None,
        "recode":      {9.0: 6.0},
        "group_labels": {
            -1.0: "Not provided",
            1.0: "Degree",              2.0: "Other higher degree",
            3.0: "A-level etc",         4.0: "GCSE etc",
            5.0: "Other qualification", 6.0: "No qualification",
        },
    },

    # -------------------------------------------------------------------------
    # 2. Employment
    # -------------------------------------------------------------------------
    "jbstat": {
        "code":        "jbstat",
        "cluster":     True,
        "label":       "Employment status",
        "categorical": True,
        "backfill":    None,
        "categories":  {
            -1.0: "Not provided",
            1.0: "Self-employed",
            2.0: "Paid employment (ft/pt)",
            3.0: "Unemployed",
            4.0: "Retired",
            5.0: "On maternity leave",
            6.0: "Family care or home",
            7.0: "Full-time student",
            8.0: "LT sick or disabled",
            9.0: "Govt training scheme",
            10.0: "Unpaid family business",
            11.0: "On apprenticeship",
            12.0: "On furlough",
            13.0: "Temporarily laid off",
            14.0: "On shared parental leave",
            15.0: "On adoption leave",
            97.0: "Doing something else",
        },
        # UKHLS negative codes: not in recode — 3a backfill maps them to -1 (“not provided”).
        "recode": {
            1.0: 1.0,
            2.0: 1.0,
            12.0: 1.0,
            13.0: 1.0,
            3.0: 3.0,
            4.0: 4.0,
            5.0: 5.0,
            6.0: 5.0,
            14.0: 5.0,
            15.0: 5.0,
            7.0: 7.0,
            9.0: 7.0,
            11.0: 7.0,
            8.0: 8.0,
            10.0: 8.0,
            97.0: 8.0,
        },
        "group_labels": {
            -1.0: "Not provided",
            1.0: "Employed",
            3.0: "Unemployed",
            4.0: "Retired",
            5.0: "On leave",
            7.0: "Student / training",
            8.0: "Inactive",
        },
        "one_hot":     True,
    },
    "marstat_dv": {
        "code":        "marstat_dv",
        "cluster":     True,
        "label":       "Marital status",
        "categorical": True,
        "backfill":    None,
        "categories":  {
            -1.0: "Not provided",
            0.0: "Under 16 years",
            1.0: "Married/Civil partner",
            2.0: "Living as couple",
            3.0: "Widowed/surviving civil partner",
            4.0: "Divorced/dissolved civil partner",
            5.0: "Separated (incl. from civil partner)",
            6.0: "Never married",
        },
        "one_hot":     True,
    },

    # -------------------------------------------------------------------------
    # 3. Household
    # -------------------------------------------------------------------------
    # UKHLS derived tenure — https://www.understandingsociety.ac.uk/documentation/mainstage/variables/tenure_dv/
    "tenure_dv": {
        "code":        "tenure_dv",
        "cluster":     True,
        "label":       "Housing tenure (Own/Rent)",
        "categorical": True,
        "backfill":    None,
        "file":        "hhresp",
        "categories":  {
            -1.0: "Not provided",
            1.0: "Owned outright",
            2.0: "Owned with mortgage",
            3.0: "Local authority rent",
            4.0: "Housing association rented",
            5.0: "Rented from employer",
            6.0: "Rented private unfurnished",
            7.0: "Rented private furnished",
            8.0: "Other",
        },
        # UKHLS negative codes: not in recode — 3a backfill maps them to -1 (“not provided”).
        "recode": {
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
            -1.0: "Not provided",
            1.0: "Owner-occupied",
            2.0: "Rented",
            3.0: "Other",
        },
        "one_hot":     True,
    },
    "hhtype_dv": {
        "code":        "hhtype_dv",
        "cluster":     True,
        "label":       "Composition of household (LFS)",
        "categorical": True,
        "backfill":    None,
        "file":        "hhresp",
        # Raw LFS codes; recode collapses gender and pension-age splits (see sex_dv, doby_dv, jbstat).
        "categories":  {
            -1.0: "Not provided",
            1.0: "1 male, aged 65+, no children",
            2.0: "1 female, age 60+, no children",
            3.0: "1 adult under pensionable age, no children",
            4.0: "1 adult, 1 child",
            5.0: "1 adult, 2 or more children",
            6.0: "Couple both under pensionable age, no children",
            8.0: "Couple 1 or more over pensionable age, no children",
            10.0: "Couple with 1 child",
            11.0: "Couple with 2 children",
            12.0: "Couple with 3 or more children",
            16.0: "2 adults, not a couple, both under pensionable age, no children",
            17.0: "2 adults, not a couple, one or more over pensionable age, no children",
            18.0: "2 adults, not a couple, 1 or more children",
            19.0: "3 or more adults, no children, incl. at least one couple",
            20.0: "3 or more adults, 1–2 children, incl. at least one couple",
            21.0: "3 or more adults, >2 children, incl. at least one couple",
            22.0: "3 or more adults, no children, excl. any couples",
            23.0: "3 or more adults, 1 or more children, excl. any couples",
        },
        # UKHLS negative codes: not in recode — 3a backfill maps them to -1 (“not provided”).
        "recode": {
            # Lone adult, no children (male 65+ / female 60+ / under PA → one type)
            1.0: 1.0,
            2.0: 1.0,
            3.0: 1.0,
            4.0: 2.0,
            5.0: 3.0,
            # Couple, no children: both under PA vs one+ over PA → one type
            6.0: 4.0,
            8.0: 4.0,
            10.0: 5.0,
            11.0: 6.0,
            12.0: 7.0,
            # Two adults not a couple: drop pension-age split
            16.0: 8.0,
            17.0: 8.0,
            18.0: 9.0,
            19.0: 10.0,
            20.0: 11.0,
            21.0: 12.0,
            22.0: 13.0,
            23.0: 14.0,
        },
        "group_labels": {
            -1.0: "Not provided",
            1.0: "1 adult, no children",
            2.0: "1 adult, 1 child",
            3.0: "1 adult, 2+ children",
            4.0: "Couple, no children",
            5.0: "Couple, 1 child",
            6.0: "Couple, 2 children",
            7.0: "Couple, 3+ children",
            8.0: "2 adults (not a couple), no children",
            9.0: "2 adults (not a couple), with children",
            10.0: "3+ adults (incl. couple), no children",
            11.0: "3+ adults (incl. couple), 1–2 children",
            12.0: "3+ adults (incl. couple), 3+ children",
            13.0: "3+ adults (no couple), no children",
            14.0: "3+ adults (no couple), with children",
        },
        "one_hot":     True,
    },



    # -------------------------------------------------------------------------
    # 5. Health & wellbeing
    # -------------------------------------------------------------------------
    # SF-12 item 1: self-rated general health (1=Excellent → 5=Poor)
    "scsf1": {
        "code":        "scsf1",
        "cluster":     True,
        "label":       "Self-rated general health",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -1.0: "Not provided",
            1.0: "Excellent",
            2.0: "Very good",
            3.0: "Good",
            4.0: "Fair",
            5.0: "Poor",
        },
        "one_hot":     False,
    },
}

# -----------------------------------------------------------------------------
# Convenience exports (same pattern as config_variables.py)
# -----------------------------------------------------------------------------

DEMOGRAPHICS_VARIABLES = VARIABLES  # alias — same object
DEMOGRAPHICS_ORDER: tuple[str, ...] = tuple(VARIABLES.keys())
VARIABLE_MAP: dict[str, str] = {k: v["label"] for k, v in VARIABLES.items()}

__all__ = [
    "VARIABLES",
    "DEMOGRAPHICS_ORDER",
    "DEMOGRAPHICS_VARIABLES",
    "VARIABLE_MAP",
]
