# data_processing/config_variables.py
#
# Single source of truth for all UKHLS variables used in this pipeline.
# Each entry is a dict with:
#   code        - base variable name (wave prefix e.g. o_ handled by ingestion)
#   label       - human-readable description
#   categorical - True if the variable is categorical, False if continuous
#   categories  - dict mapping raw numeric code (float) -> English label, or None
#   group_labels- (optional) post-recode display labels {canonical_code -> label};
#                 overrides categories in CATEGORY_MAPS when present
#   fill        - imputation strategy: "mode" | "median" | "zero" | None
#   cluster     - True if this variable should be used as a K-Means feature
#   one_hot     - list of category codes (float) to one-hot encode, or None
#   clip        - (optional) upper bound to clip outliers before clustering/viz
#   floor       - (optional) lower bound to clip (e.g. 0 to zero-out negative pay)
#   recode      - (optional) dict of {raw_value -> new_value} applied before use
#   bin_width   - (optional) fixed histogram bin width for visualisation (overrides auto-binning)

VARIABLES = {

    # -------------------------------------------------------------------------
    # 0. Anchors & Processing  (never clustered — identifiers / raw sources)
    # -------------------------------------------------------------------------
    "pidp": {
        "code":        "pidp",
        "label":       "Unique Person ID (anchor for all joins)",
        "categorical": False,
        "categories":  None,
        "fill":        None,
        "cluster":     False,
        "one_hot":     None,
    },
    #"disdif": {
    #    "code":        "disdif",
    #    "label":       "Disability indicator (multi-response 1-96)",
    #    "categorical": True,
    #    "categories":  None,   # exploded into disability_* columns downstream
    #    "fill":        None,
    #    "cluster":     False,
    #    "one_hot":     None,   # handled separately by DISABILITY_LABELS expansion
    #},

    # -------------------------------------------------------------------------
    # 1. Core Demographics
    # -------------------------------------------------------------------------
    "age_dv": {
        "code":        "age_dv",
        "label":       "Derived age at interview",
        "categorical": False,
        "categories":  None,
        "fill":        0,
        "cluster":     True,
        "one_hot":     None,
    },
    "sex_dv": {
        "code":        "sex_dv",
        "label":       "Gender",
        "categorical": True,
        "categories":  {1.0: "Male", 2.0: "Female", 0.0: "Not known"},
        "fill":        0.0,
        "cluster":     False,  
        "one_hot":     [1.0],
    },
    "englang": { # unless respondent stated specifically, assume English is their first language (most common category) rather than treating as missing
        "code":        "englang",
        "label":       "English is not first language",
        "categorical": True,
        "categories":  {1.0: "Yes", 2.0: "No"},
        "fill":        1.0,
        "cluster":     True,   # OHE to englang_1 used as cluster feature
        "one_hot":     [2.0],
    },
    "oprlg1": {
        "code":        "oprlg1",
        "label":       "Religion",
        "categorical": True,
        # ── all raw codes as they appear in the UKHLS data ───────────────
        "categories":  {
            -8.0: "Inapplicable",
             2.0: "Christian (no denomination)",
             3.0: "Roman Catholic",
             4.0: "Church of Scotland",
             7.0: "Methodist",
             8.0: "Baptist",
            10.0: "Other Christian",
            11.0: "Christian (no specific denomination)",
            12.0: "Muslim/Islam",
            13.0: "Hindu",
            14.0: "Jewish",
            15.0: "Sikh",
            16.0: "Buddhist",
            97.0: "Other",
        },
        # ── collapse all Christian denominations into one code ────────────
        "recode": {
             3.0: 2.0,   # Roman Catholic                      → 2 (Christian)
             4.0: 2.0,   # Church of Scotland                  → 2 (Christian)
             7.0: 2.0,   # Methodist                           → 2 (Christian)
             8.0: 2.0,   # Baptist                             → 2 (Christian)
            10.0: 2.0,   # Other Christian                     → 2 (Christian)
            11.0: 2.0,   # Christian (no specific denomination)→ 2 (Christian)
        },
        # ── display labels for post-recode canonical codes ────────────────
        "group_labels": {
            -8.0: "None/Not applicable",
             2.0: "Christian",
            12.0: "Muslim/Islam",
            13.0: "Hindu",
            14.0: "Jewish",
            15.0: "Sikh",
            16.0: "Buddhist",
            97.0: "Other",
        },
        "fill":        -8.0,
        "cluster":     False,  # kept in profile output but excluded from distance calc
        "one_hot":     True,
    },

    # -------------------------------------------------------------------------
    # 2. Socioeconomic & Education
    # -------------------------------------------------------------------------
    "hiqual_dv": {
        "code":        "hiqual_dv",
        "label":       "Highest qualification",
        "categorical": False,  # ordinal scale — treated as continuous for clustering but categorical for labelling
        "categories":  {
            1.0: "Degree",       2.0: "Other Higher",
            3.0: "A-Level",      4.0: "GCSE",
            5.0: "Other / None",
        },
        "fill":        5.0,
        "cluster":     True,
        "one_hot":     None,
        "recode":      {9.0: 5.0},  # "None" (9) → 5 to keep scale 1–5
    },
    "payn_dv": {
        "code":        "payn_dv",
        "label":       "Monthly net pay (take-home)",
        "categorical": False,
        "categories":  None,
        "fill":        0,
        "cluster":     True,
        "one_hot":     None,
        "floor":       0,    # non-positive values (inapplicable/not in work) → 0
        "clip":        8000,  # caps extreme outliers that distort clustering
    },
    "fimngrs_dv": {
        "code":        "fimngrs_dv",
        "label":       "Total monthly personal income (gross)",
        "categorical": False,
        "categories":  None,
        "fill":        0.0,
        "cluster":     True,
        "one_hot":     None,
        "floor":       0,    # non-positive values (inapplicable/not in work) → 0
        "clip":        8000, 
          # caps extreme outliers that distort clustering
    },    
    "jbnssec8_dv": {
        "code":        "jbnssec8_dv",
        "label":       "Social class (NS-SEC 8)",
        "categorical": False,  # ordinal scale — treated as continuous
        "categories":  {
            -9.0: "Missing",
            0.0: "Unknown",
            1.0: "Large employers & higher management",
            2.0: "Higher professional",
            3.0: "Lower management & professional",
            4.0: "Intermediate",
            5.0: "Small employers & own account",
            6.0: "Lower supervisory & technical",
            7.0: "Semi-routine",
            8.0: "Routine",
        },
        "recode": {-9.0: 0.0},
        "fill":        "mode",
        "cluster":     True,
        "one_hot":     None,
    },


    # -------------------------------------------------------------------------
    # 3. Household & Environment
    # -------------------------------------------------------------------------
    "hhsize": {
        "code":        "hhsize",
        "label":       "Household size",
        "categorical": False,
        "categories":  None,
        "fill":        1,
        "cluster":     True,
        "one_hot":     None,
    },
    "nchild_dv": {
        "code":        "nchild_dv",
        "label":       "Number of own children in household",
        "categorical": False,
        "categories":  None,
        "fill":        0,
        "cluster":     True,
        "one_hot":     None,
        'floor':       0,    
        'clip':        7,   # caps extreme outliers that distort clustering
    },

    # -------------------------------------------------------------------------
    # 4. Health & Wellbeing
    # -------------------------------------------------------------------------
    "sf12mcs_dv": {
        "code":        "sf12mcs_dv",
        "label":       "Mental health score (SF-12 MCS)",
        "categorical": False,
        "categories":  None,
        "fill":        "median",
        "cluster":     True,
        "one_hot":     None,
    },
    "sf12pcs_dv": {
        "code":        "sf12pcs_dv",
        "label":       "Physical health score (SF-12 PCS)",
        "categorical": False,
        "categories":  None,
        "fill":        "median",
        "cluster":     True,
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 5. Community & Local Services
    # -------------------------------------------------------------------------
    "nbrsnci_dv": {
        "code":        "nbrsnci_dv",
        "label":       "Buckner Neighbourhood Cohesion Index",
        "categorical": True,
        "categories":  None,
        "fill":        "median",
        "cluster":     False,
        "one_hot":     None,
        "bin_width":   1,   # show as 5 count-bars: 0-1, 1-2, 2-3, 3-4, 4-5
    },
    "locsera": {
        "code":        "locsera",
        "label":       "Standard of local services: Schools",
        "categorical": False,  # ordinal scale — treated as continuous
        "categories":  {
            1.0: "Excellent", 2.0: "Good", 3.0: "Fair",
            4.0: "Poor",      5.0: "Very Poor/Bad",
        },
        "fill":        "mode",
        "cluster":     False,
        "one_hot":     None,
    },
    "locserc": {
        "code":        "locserc",
        "label":       "Standard of local services: Public transport",
        "categorical": False,  # ordinal scale — treated as continuous
        "categories":  {
            1.0: "Excellent", 2.0: "Good", 3.0: "Fair",
            4.0: "Poor",      5.0: "Very Poor/Bad",
        },
        "fill":        "mode",
        "cluster":     False,
        "one_hot":     None,
    },
    "locserd": {
        "code":        "locserd",
        "label":       "Standard of local services: Shopping",
        "categorical": False,  # ordinal scale — treated as continuous
        "categories":  {
            1.0: "Excellent", 2.0: "Good", 3.0: "Fair",
            4.0: "Poor",      5.0: "Very Poor/Bad",
        },
        "fill":        "mode",
        "cluster":     False,
        "one_hot":     None,
    },
    "locsere": {
        "code":        "locsere",
        "label":       "Standard of local services: Leisure",
        "categorical": False,  # ordinal scale — treated as continuous
        "categories":  {
            1.0: "Excellent", 2.0: "Good", 3.0: "Fair",
            4.0: "Poor",      5.0: "Very Poor/Bad",
        },
        "fill":        "mode",
        "cluster":     False,
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 6. Transport Habits
    # -------------------------------------------------------------------------
    "jbttwt": {
        "code":        "jbttwt",
        "label":       "Minutes spent travelling to work",
        "categorical": False,
        "categories":  None,
        "fill":        "zero",
        "cluster":     False,
        "one_hot":     None,
        "clip":        120,   # caps extreme outliers that distort clustering
    },
    "envhabit8": {
        "code":        "envhabit8",
        "label":       "Environmental habit: public transport use",
        "categorical": False,  # ordinal scale — treated as continuous
        "categories":  {
            1.0: "Always",        2.0: "Very often",
            3.0: "Quite often",   4.0: "Not very often",
            5.0: "Never",
        },
        "fill":        "mode",
        "cluster":     False,
        "one_hot":     None,
    },
    "carmiles": {
        "code":        "carmiles",
        "label":       "Miles driven in last 12 months",
        "categorical": False,
        "categories":  None,
        "fill":        "zero",
        "cluster":     False,
        "one_hot":     None,
        "floor":       0,    # non-positive values (inapplicable/no car) → 0
        "clip":        50_000,  # ~1,000 miles/week — clips erroneous entries
    },
    "caruse": {
        "code":        "caruse",
        "label":       "Has use of a car or van",
        "categorical": True,
        "categories":  {1.0: "Yes", 2.0: "No"},
        "fill":        2.0,   
        "cluster":     False,  
        "one_hot":     None,
    },
    "jbpl": {
        "code":        "jbpl",
        "label":       "Work location",
        "categorical": True,
        "categories":  {
            1.0: "At home",          2.0: "Employer premises",
            3.0: "Driving/travel",   4.0: "Various",
        },
        "fill":        "mode",
        "cluster":     True,   # OHE to jbpl_1 used as cluster feature (works at home)
        "one_hot":     [1.0],
    },
    "wktrvfar": {
        "code":        "wktrvfar",
        "label":       "Main mode of transport to work",
        "categorical": True,
        "categories":  {
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
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
        "cluster":     False,   # OHE to wktrvfar_1 used as cluster feature (drives to work)
        "one_hot":     [1.0],
        "group_labels": {
             1.0: "Drives to work",
        }
    },  

    # -------------------------------------------------------------------------
    # 7. Job Detail  (context variables — not direct cluster features)
    # -------------------------------------------------------------------------
    "jbstat": {
        "code":        "jbstat",
        "label":       "Employment status",
        "categorical": True,
        # ── all raw codes as they appear in the UKHLS data ───────────────
        "categories":  {
            -9.0: "Missing",
            -2.0: "Refusal",
            -1.0: "Don't know",
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
        # ── collapse raw codes into 6 canonical groups for clustering ─────
        # After recode, only these 6 codes remain: 1, 3, 4, 5, 7, 8
        "recode": {
             2.0: 1.0,   # paid employment        → 1  (Employed)
            11.0: 7.0,   # apprenticeship         → 7  (Student / training)
            12.0: 1.0,   # furlough               → 1  (Employed)
            13.0: 1.0,   # temporarily laid off   → 1  (Employed)
             6.0: 5.0,   # family care            → 5  (On leave)
            14.0: 5.0,   # shared parental leave  → 5  (On leave)
            15.0: 5.0,   # adoption leave         → 5  (On leave)
             9.0: 7.0,   # govt training          → 7  (Student)
            10.0: 8.0,   # unpaid family business → 8  (Inactive)
            97.0: 8.0,   # doing something else   → 8  (Inactive)
            -1.0: 8.0,   # don't know             → 8  (Inactive)
            -2.0: 8.0,   # refusal                → 8  (Inactive)
            -9.0: 8.0,   # missing                → 8  (Inactive)
        },
        # ── display labels for the 6 post-recode canonical codes ──────────
        # Used by build_dna_row / CATEGORY_MAPS in place of raw categories.
        "group_labels": {
            1.0: "Employed",
            3.0: "Unemployed",
            4.0: "Retired",
            5.0: "On leave",
            7.0: "Student / training",
            8.0: "Inactive",
        },
        "fill":        "mode",
        "cluster":     True,  # raw column not a cluster feature; OHE columns (jbstat_*) are used downstream
        "one_hot":     True,
    },
    #"jlsic07_cc": {
    #    "code":        "jlsic07_cc",
    #    "label":       "Last job: SIC 2007 industry (condensed)",
    #    "categorical": True,
    #    "categories":  None,   # too granular for direct labelling
    #    "fill":        "mode",
    #    "cluster":     False,
    #    "one_hot":     None,
    #},
    #"socialkid": {
    #    "code":        "socialkid",
    #    "label":       "Frequency of leisure activities with child",
    #    "categorical": True,
    #    "categories":  None,
    #    "fill":        "mode",
    #    "cluster":     False,
    #    "one_hot":     None,
    #},

    # -------------------------------------------------------------------------
    # 8. Derived / Engineered Variables  (already binary 0/1 — no one-hot needed)
    # -------------------------------------------------------------------------
    # "disability_mobility": {
    #     "code":        "disability_mobility",
    #     "label":       "Disability: Mobility",
    #     "categorical": True,
    #     "categories":  {1.0: "Yes", 0.0: "No"},
    #     "fill":        "zero",
    #     "cluster":     True,
    #     "one_hot":     None,
    # },
    # "disability_visual": {
    #     "code":        "disability_visual",
    #     "label":       "Disability: Visual",
    #     "categorical": True,
    #     "categories":  {1.0: "Yes", 0.0: "No"},
    #     "fill":        "zero",
    #     "cluster":     True,
    #     "one_hot":     None,
    # },
    # "disability_hearing": {
    #     "code":        "disability_hearing",
    #     "label":       "Disability: Hearing",
    #     "categorical": True,
    #     "categories":  {1.0: "Yes", 0.0: "No"},
    #     "fill":        "zero",
    #     "cluster":     True,
    #     "one_hot":     None,
    # },
    # "disability_learning": {
    #     "code":        "disability_learning",
    #     "label":       "Disability: Learning",
    #     "categorical": True,
    #     "categories":  {1.0: "Yes", 0.0: "No"},
    #     "fill":        "zero",
    #     "cluster":     True,
    #     "one_hot":     None,
    # },
    # "disability_mental_health": {
    #     "code":        "disability_mental_health",
    #     "label":       "Disability: Mental Health",
    #     "categorical": True,
    #     "categories":  {1.0: "Yes", 0.0: "No"},
    #     "fill":        "zero",
    #     "cluster":     True,
    #     "one_hot":     None,
    # },
    # "disability_dexterity": {
    #     "code":        "disability_dexterity",
    #     "label":       "Disability: Manual Dexterity",
    #     "categorical": True,
    #     "categories":  {1.0: "Yes", 0.0: "No"},
    #     "fill":        "zero",
    #     "cluster":     True,
    #     "one_hot":     None,
    # },
    # "disability_memory": {
    #     "code":        "disability_memory",
    #     "label":       "Disability: Memory",
    #     "categorical": True,
    #     "categories":  {1.0: "Yes", 0.0: "No"},
    #     "fill":        "zero",
    #     "cluster":     True,
    #     "one_hot":     None,
    # },

    # -------------------------------------------------------------------------
    # 9. Target Binary Classification States  (outputs, not clustering inputs)
    # One binary column per jbstat canonical group (code matches after recode).
    # -------------------------------------------------------------------------
    #"alljbstat1": {
    #    "code":        "alljbstat1",
    #    "label":       "Employed",
    #    "categorical": True,
    #    "categories":  {1.0: "Yes", 0.0: "No"},
    #    "fill":        "zero",
    #    "cluster":     False,  # group-filter column — excluded from K-Means distance
    #    "one_hot":     None,
    #    "summary":     True,
    #},
    #"alljbstat3": {
    #    "code":        "alljbstat3",
    #    "label":       "Unemployed",
    #    "categorical": True,
    #    "categories":  {1.0: "Yes", 0.0: "No"},
    #    "fill":        "zero",
    #    "cluster":     True,
    #    "one_hot":     None,
    #    "summary":     True,
    #},
    #"alljbstat4": {
    #    "code":        "alljbstat4",
    #    "label":       "Retired",
    #    "categorical": True,
    #    "categories":  {1.0: "Yes", 0.0: "No"},
    #    "fill":        "zero",
    #    "cluster":     True,
    #    "one_hot":     None,
    #    "summary":     True,
    #},
    #"alljbstat5": {
    #    "code":        "alljbstat5",
    #    "label":       "On leave",
    #    "categorical": True,
    #    "categories":  {1.0: "Yes", 0.0: "No"},
    #    "fill":        "zero",
    #    "cluster":     True,
    #    "one_hot":     None,
    #    "summary":     True,
    #},
    #"alljbstat7": {
    #    "code":        "alljbstat7",
    #    "label":       "Student",
    #    "categorical": True,
    #    "categories":  {1.0: "Yes", 0.0: "No"},
    #    "fill":        "zero",
    #    "cluster":     True,
    #    "one_hot":     None,
    #    "summary":     True,
    #},
    #"alljbstat8": {
    #    "code":        "alljbstat8",
    #    "label":       "Inactive",
    #    "categorical": True,
    #    "categories":  {1.0: "Yes", 0.0: "No"},
    #    "fill":        "zero",
    #    "cluster":     True,
    #    "one_hot":     None,
    #    "summary":     True,
    #},
}

# -----------------------------------------------------------------------------
# Convenience accessors derived from VARIABLES (single source of truth)
# -----------------------------------------------------------------------------

# code -> label  (mirrors old VARIABLE_MAP)
VARIABLE_MAP = {k: v["label"] for k, v in VARIABLES.items()}

# code -> category dict used for display (group_labels takes precedence over
# categories when present — allows raw categories to document all codes while
# group_labels reflects post-recode canonical values)
CATEGORY_MAPS = {
    k: v.get("group_labels") or v["categories"]
    for k, v in VARIABLES.items()
    if v["categorical"] and (v.get("group_labels") or v["categories"]) is not None
}

# Sets of codes by type
CATEGORICAL_VARS = {k for k, v in VARIABLES.items() if v["categorical"]}
CONTINUOUS_VARS  = {k for k, v in VARIABLES.items() if not v["categorical"]}

# Variables used as K-Means features (cluster=True)
CLUSTER_VARS = [k for k, v in VARIABLES.items() if v["cluster"]]

# Variables shown in the regional cluster summary table (all variables now included)
SUMMARY_VARS = list(VARIABLES.keys())

# Variables to one-hot encode: code -> list of float category codes
# Use pd.get_dummies or equivalent with these column subsets
ONE_HOT_VARS = {
    k: v["one_hot"]
    for k, v in VARIABLES.items()
    if v["one_hot"] is not None
}

# Fill strategy lookup: code -> "mode" | "median" | "zero" | None
FILL_STRATEGIES = {k: v["fill"] for k, v in VARIABLES.items()}

# Upper-clip values for outlier-prone continuous variables: code -> numeric upper bound
CLIP_VALUES = {k: v["clip"] for k, v in VARIABLES.items() if v.get("clip") is not None}

# Lower-floor values: code -> numeric lower bound (values below this are set to floor)
FLOOR_VALUES = {k: v["floor"] for k, v in VARIABLES.items() if v.get("floor") is not None}

# Fixed histogram bin widths for visualisation: code -> bin width
BIN_WIDTHS = {k: v["bin_width"] for k, v in VARIABLES.items() if v.get("bin_width") is not None}

# Value recoding: code -> {old_value: new_value} applied before clustering/viz
RECODE_MAPS = {k: v["recode"] for k, v in VARIABLES.items() if v.get("recode") is not None}

# Disability one-hot label mapping (used when expanding o_disdif1..96)
DISABILITY_LABELS = {
    "1":  "mobility",       "2":  "visual",        "3":  "hearing",
    "4":  "learning",       "5":  "mental_health",  "6":  "dexterity",
    "7":  "stamina",        "8":  "memory",         "9":  "behavioral",
    "10": "progressive",    "11": "other",          "96": "other",
}
