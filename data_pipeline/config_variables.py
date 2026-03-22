# data_pipeline/config_variables.py
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
#   backfill    - list of values that trigger a look-back through older waves (e.g.
#                 [-9, -7, -2, -1]); NaN always triggers if a list is provided.
#                 Use None or [] to disable backfill for this variable.
#   xwave       - (optional) True if this variable should be sourced from xwavedat.pkl
#                 (looked up by code); xwave vars are never backfilled
#   transform   - (optional) transformation applied during feature engineering, e.g.
#                 "birth_year_to_age"

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
        "backfill":    None,
    },

    # =========================================================================
    # CLUSTER FEATURES  (cluster: True — used directly as K-Means inputs)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 1. Demographics
    # -------------------------------------------------------------------------
    "doby_dv": {
        "code":        "doby_dv",
        "label":       "Age in years",
        "categorical": False,
        "categories":  None,
        "fill":        0,
        "cluster":     True,
        "one_hot":     None,
        "backfill":    None,
        "xwave":       True,
        "transform":   "birth_year_to_age",
    },
        "sex_dv": { # very few missing values, so no need to remap
        "code":        "sex_dv",
        "label":       "Gender",
        "categorical": True,
        "backfill":    None,
        "categories":  {-20.0: "No data from BHPS", -9.0: "Missing", 0.0: "Inconsistent", 1.0: "Male", 2.0: "Female"},
        "fill":        0.0,
        "cluster":     True,
        "xwave":       True,
    },


    "ff_oprlg1": {
        "code":        "ff_oprlg1",
        "label":       "Religion",
        "categorical": True,
        "backfill":    [-9, -8, -2, -1],
        # ── all raw codes as they appear in the UKHLS data ───────────────
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -1.0: "Missing / not stated",
             2.0: "Church of England/Anglican",
             3.0: "Roman Catholic",
             4.0: "Church of Scotland",
             5.0: "Free Church / Free Presbyterian",
             6.0: "Episcopalian",
             7.0: "Methodist",
             8.0: "Baptist",
             9.0: "Congregational / URC",
            10.0: "Other Christian",
            11.0: "Christian (no denomination)",
            12.0: "Muslim/Islam",
            13.0: "Hindu",
            14.0: "Jewish",
            15.0: "Sikh",
            16.0: "Buddhist",
            17.0: "Church of Wales",
            97.0: "Other",
        },
        # ── collapse all Christian denominations into one code ────────────
        "recode": {
            -9.0: 1,  # not religious                             
            -8.0: 1,  # not religious    
            -1.0: 1,  # not religious    
             3.0: 2.0,   # Roman Catholic                      → 2 (Christian)
             4.0: 2.0,   # Church of Scotland                  → 2 (Christian)
             5.0: 2.0,   # Free Church / Free Presbyterian     → 2 (Christian)
             6.0: 2.0,   # Episcopalian                        → 2 (Christian)
             7.0: 2.0,   # Methodist                           → 2 (Christian)
             8.0: 2.0,   # Baptist                             → 2 (Christian)
             9.0: 2.0,   # Congregational / URC                → 2 (Christian)
            10.0: 2.0,   # Other Christian                     → 2 (Christian)
            11.0: 2.0,   # Christian (no denomination)          → 2 (Christian)
            17.0: 2.0,   # Church of Wales                     → 2 (Christian)
            97.0: 17.0,  # Other                               → inapplicable
        },
        # ── display labels for post-recode canonical codes ────────────────
        "group_labels": {
            1.0: "Not religious",
            2.0: "Christian",
            12.0: "Muslim/Islam",
            13.0: "Hindu",
            14.0: "Jewish",
            15.0: "Sikh",
            16.0: "Buddhist",
            17.0: "Other",
        },
        "fill":        1.0,
        "cluster":     True,
        "one_hot":     True,
    },
    "racel_dv": {
        "code":        "racel_dv",
        "label":       "Ethnic group",
        "xwave":       True,
        "categorical": True,
        "backfill":    None,
        # ── all raw codes as they appear in the UKHLS data ───────────────
        "categories":  {
            -9.0: "Missing",
             1.0: "White: British/English/Scottish/Welsh/N. Irish",
             2.0: "White: Irish",
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
        # ── collapse into 8 canonical groups ─────────────────────────────
        "recode": {
            -9.0:  0.0,   # missing                             → 0 (Not stated)
            # ── White / Mixed (1) ─────────────────────────────────────────
             1.0:  1.0,   # White British etc.                  → 1
             2.0:  1.0,   # White Irish                         → 1
             4.0:  1.0,   # White Other                         → 1
             5.0:  1.0,   # Mixed: White and Black Caribbean    → 1
             6.0:  1.0,   # Mixed: White and Black African      → 1
             7.0:  1.0,   # Mixed: White and Asian              → 1
             8.0:  1.0,   # Mixed: Other                        → 1
            # ── Indian (2) ────────────────────────────────────────────────
             9.0:  2.0,   # Asian: Indian                       → 2
            # ── Pakistani / Bangladeshi (3) ───────────────────────────────
            10.0:  3.0,   # Asian: Pakistani                    → 3
            11.0:  3.0,   # Asian: Bangladeshi                  → 3
            # ── Other Asian (4) ───────────────────────────────────────────
            12.0:  4.0,   # Asian: Chinese                      → 4
            13.0:  4.0,   # Asian: Other Asian                  → 4
            # ── Arab (5) ──────────────────────────────────────────────────
            17.0:  5.0,   # Arab                                → 5
            # ── Caribbean (6) ─────────────────────────────────────────────
            14.0:  6.0,   # Black: Caribbean                    → 6
            # ── African (7) ───────────────────────────────────────────────
            15.0:  7.0,   # Black: African                      → 7
            # ── Other (8) ─────────────────────────────────────────────────
            16.0:  7.0,   # Black: Other                        → 7
            97.0:  8.0,   # Other ethnic group                  → 8
        },
        # ── display labels for post-recode canonical codes ────────────────
        "group_labels": {
            0.0: "Not stated",
            1.0: "White / Mixed",
            2.0: "Indian",
            3.0: "Pakistani / Bangladeshi",
            4.0: "Other Asian",
            5.0: "Arab",
            6.0: "Caribbean",
            7.0: "African",
            8.0: "Other",
        },
        "fill":    0,
        "cluster": True,
        "one_hot": True,
    },
    "englang": {
        "code":        "englang",
        "label":       "English is my first language",
        "categorical": True,
        "categories":  {-9.0: "Missing", -7.0: "Proxy", -2.0: "Refusal", -1.0: "Don't know", 1.0: "Yes", 2.0: "No"},
        "recode":      {
            -9.0: 1.0,  # Missing          → Yes (assume English)
            -8.0: 1.0,  # Inapplicable     → Yes (assume English)
            -7.0: 1.0,  # Proxy            → Yes (assume English)
            -2.0: 1.0,  # Refusal          → Yes (assume English)
            -1.0: 1.0,  # Don't know       → Yes (assume English)
        },
        "group_labels": {1.0: "Yes", 2.0: "No"},
        "fill":        1.0,
        "cluster":     True,
        "backfill":    [-9, -8, -7, -2, -1],
    },
    # -------------------------------------------------------------------------
    # 2. Socioeconomic
    # -------------------------------------------------------------------------
    "hiqual_dv": {
        "code":        "hiqual_dv",
        "label":       "Highest qualification",
        "categorical": False,  # ordinal scale — treated as continuous for clustering but categorical for labelling
        "backfill":    [-9, -8, -2, -1],
        "categories":  {
            -9.0: "Missing",     -8.0: "Inapplicable",
            -2.0: "Refusal",     -1.0: "Don't know",
             1.0: "Degree",       2.0: "Other higher degree",
             3.0: "A-level etc",  4.0: "GCSE etc",
             5.0: "Other qualification", 9.0: "No qualification",
        },
        "fill":        5.0,
        "cluster":     True,
        "one_hot":     None,
        "recode":      {9.0: 6.0},  # "No qualification" (9) → 6
        "group_labels": {
            1.0: "Degree",              2.0: "Other higher degree",
            3.0: "A-level etc",         4.0: "GCSE etc",
            5.0: "Other qualification", 6.0: "No qualification",
        },
    },
    "fimngrs_dv": {
        "code":        "fimngrs_dv",
        "label":       "Total monthly personal income (gross)",
        "categorical": False,
        "backfill":    None, #we want their current income  
        "categories":  None,
        "fill":        0.0,
        "cluster":     True,
        "one_hot":     None,
        "floor":       0,    # non-positive values (inapplicable/not in work) → 0
        "clip":        8000, # caps extreme outliers that distort clustering
    },
    "jbnssec8_dv": {
        "code":        "jbnssec8_dv",
        "label":       "Job type (NS-SEC 8)",
        "categorical": False,  # ordinal scale — treated as continuous
        "backfill":    None, # we want their current job type  
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy respondent",
            -2.0: "Refusal",
            -1.0: "Don't know",
             1.0: "Large employers & higher management",
             2.0: "Higher professional",
             3.0: "Lower management & professional",
             4.0: "Intermediate",
             5.0: "Small employers & own account",
             6.0: "Lower supervisory & technical",
             7.0: "Semi-routine",
             8.0: "Routine",
        },
        "recode": {
            -9.0: 0.0,  # missing       → 0 (Unknown)
            -8.0: 0.0,  # inapplicable  → 0 (Unknown; non-employed so no NS-SEC)
            -7.0: 0.0,  # proxy         → 0 (Unknown)
            -2.0: 0.0,  # refusal       → 0 (Unknown)
            -1.0: 0.0,  # don't know    → 0 (Unknown)
        },
        "group_labels": {
            0.0: "Unknown / not applicable",
            1.0: "Large employers & higher management",
            2.0: "Higher professional",
            3.0: "Lower management & professional",
            4.0: "Intermediate",
            5.0: "Small employers & own account",
            6.0: "Lower supervisory & technical",
            7.0: "Semi-routine",
            8.0: "Routine",
        },
        "fill":        "mode",
        "cluster":     True,
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 3. Household
    # -------------------------------------------------------------------------
    "nchild_dv": {
        "code":        "nchild_dv",
        "label":       "Number of own children in household",
        "categorical": False,
        "backfill":    None,
        "categories":  None,
        "fill":        0,
        "cluster":     True, 
        "one_hot":     None,
        'floor':       0,
        'clip':        7,
        'create_binary_derrived_feature': {
            'feature_name': 'has_child',
            'threshold': 0,
            'cluster': True,
        } 
    },
    "has_child": { # binary feature derived from nchild_dv > 0, included as a cluster feature because it might capture different information than just the count of children (e.g. presence of any children vs none might be more relevant for clustering than the exact number)
        "code":        "has_child",
        "label":       "Has children",
        "categorical": False,
        "backfill":    None,
        "categories":  None,
        "fill":        0,
        "cluster":     True,   # binary 0/1 derived from nchild_dv > 0
        "one_hot":     None,
    },

    # =========================================================================
    # CONTEXT VARIABLES  (cluster: False — profiling / display only)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 5. Household & Environment
    # -------------------------------------------------------------------------
    "hhsize": {
        "code":        "hhsize",
        "label":       "Household size",
        "categorical": False,
        "backfill":    None, # we want their current household size
        "categories":  None,
        "fill":        1,
        "cluster":     True,
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 6. Income
    # -------------------------------------------------------------------------
    "payn_dv": {
        "code":        "payn_dv",
        "label":       "Monthly net pay (take-home)",
        "categorical": False,
        "backfill":    None, # we want their current payn_dv (net pay) rather than fimngrs_dv (gross income) for profiling, even though gross income is used for clustering due to less missingness
        "categories":  None,
        "fill":        0,
        "cluster":     False,
        "one_hot":     None,
        "floor":       0,    # non-positive values (inapplicable/not in work) → 0
        "clip":        8000,  # caps extreme outliers that distort clustering
    },

    "payo_dv": {
        "code":        "payo_dv",
        "label":       "Personal income — administrative / derived (UKHLS)",
        "categorical": False,
        "backfill":    [-9, -7, -2, -1],
        "categories":  None,
        "fill":        0,
        "cluster":     False,
        "one_hot":     None,
        "floor":       0,
    },
    "hiquao_dv": {
        "code":        "hiquao_dv",
        "label":       "Highest qualification — administrative / derived (UKHLS)",
        "categorical": False,
        "backfill":    [-9, -7, -2, -1],
        "categories":  None,
        "fill":        5.0,
        "cluster":     False,
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 7. Health & Wellbeing
    # -------------------------------------------------------------------------
    "sf12mcs_dv": {
        "code":        "sf12mcs_dv",
        "label":       "Mental health score (SF-12 MCS)",
        "categorical": False,
        "backfill":    [-9, -7, -2, -1],
        "categories":  None,
        "fill":        "median",
        "cluster":     False,
        "one_hot":     None,
    },
    "sf12pcs_dv": {
        "code":        "sf12pcs_dv",
        "label":       "Physical health score (SF-12 PCS)",
        "categorical": False,
        "backfill":    [-9, -7, -2, -1],
        "categories":  None,
        "fill":        "median",
        "cluster":     False,
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 8. Community & Local Services
    # -------------------------------------------------------------------------
    "nbrsnci_dv": {
        "code":        "nbrsnci_dv",
        "label":       "Buckner Neighbourhood Cohesion Index",
        "categorical": True,
        "backfill":    [-9, -7, -2, -1],
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
        "backfill":    [-9, -7, -2, -1],
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
        "backfill":    [-9, -7, -2, -1],
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
        "backfill":    [-9, -7, -2, -1],
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
        "backfill":    [-9, -7, -2, -1],
        "categories":  {
            1.0: "Excellent", 2.0: "Good", 3.0: "Fair",
            4.0: "Poor",      5.0: "Very Poor/Bad",
        },
        "fill":        "mode",
        "cluster":     False,
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 9. Digital Habits
    # -------------------------------------------------------------------------
    "netpusenew": {
        "code":        "netpusenew",
        "label":       "Internet use frequency",
        "categorical": True,
        "backfill":    None, # we want their current internet use rather than backfilling from other waves where they might have been offline
        "categories":  {
            -8.0: "Inapplicable",
            -1.0: "Missing / not stated",
             1.0: "Every day",
             2.0: "Several times a week",
             3.0: "About once a week",
             4.0: "Several times a month",
             5.0: "About once a month",
             6.0: "Less often",
             7.0: "Never",
             8.0: "No internet access",
             9.0: "No home internet",
        },
        "recode": {
            -8.0: 7.0,   # inapplicable → Never
            -1.0: 7.0,   # missing / not stated → Never
        },
        "fill":        "mode",
        "cluster":     False,
        "one_hot":     None,
    },

    # -------------------------------------------------------------------------
    # 10. Transport Habits
    # -------------------------------------------------------------------------
    "jbttwt": {
        "code":        "jbttwt",
        "label":       "Minutes spent travelling to work",
        "categorical": False,
        "backfill":    [-9, -7, -2, -1],
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
        "backfill":    [-9, -7, -2, -1],
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
        "backfill":    None, # we want their current car miles rather than backfilling from other waves where they might have been driving more/less
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
        "backfill":    None, # we want their current car use rather than backfilling from other waves where they might have had different access to a car
        "categories":  {1.0: "Yes", 2.0: "No"},
        "fill":        2.0,
        "cluster":     False,
        "one_hot":     None,
    },
    "jbpl": {
        "code":        "jbpl",
        "label":       "Work location",
        "categorical": True,
        "backfill":    None, # we want their current work location rather than backfilling from other waves where they might have been working somewhere else (e.g. at home during lockdown but not in other waves)
        "categories":  {
            1.0: "At home",          2.0: "Employer premises",
            3.0: "Driving/travel",   4.0: "Various",
        },
        "fill":        "mode",
        "cluster":     False,
        "one_hot":     [1.0],
    },
    "wktrvfar": {
        "code":        "wktrvfar",
        "label":       "Main mode of transport to work",
        "categorical": True,
        "backfill":    None,  # we want their current transport mode rather than backfilling from other waves where they might have been using different modes (e.g. not driving during lockdown but driving in other waves)
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
        "cluster":     False,
        "one_hot":     [1.0],
        "group_labels": {
             1.0: "Drives to work",
        }
    },

    # -------------------------------------------------------------------------
    # 10. Employment
    # -------------------------------------------------------------------------
    "jbstat": {
        "code":        "jbstat",
        "label":       "Employment status",
        "code":        "jbstat",
        "label":       "Employment status",
        "categorical": True,
        "backfill":    None, # we want their current employment status rather than backfilling from other waves where they might have had different employment status (e.g. employed in some waves but unemployed/retired in others)
        # ── all raw codes as they appear in the UKHLS data ───────────────
        "categories":  {
            -8.0: "Inapplicable",
            -1.0: "Missing / not stated",
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
        # All 18 raw codes are mapped explicitly below.
        # Canonical codes after recode: 1=Employed, 3=Unemployed, 4=Retired,
        #                               5=On leave, 7=Student, 8=Inactive
        "recode": {
            # ── Employed (1) ─────────────────────────────────────────────
             1.0: 1.0,   # self-employed          → 1  (Employed)
             2.0: 1.0,   # paid employment (ft/pt)→ 1  (Employed)
            12.0: 1.0,   # furlough               → 1  (Employed)
            13.0: 1.0,   # temporarily laid off   → 1  (Employed)
            # ── Unemployed (3) ───────────────────────────────────────────
             3.0: 3.0,   # unemployed             → 3  (Unemployed)
            # ── Retired (4) ──────────────────────────────────────────────
             4.0: 4.0,   # retired                → 4  (Retired)
            # ── On leave (5) ─────────────────────────────────────────────
             5.0: 5.0,   # maternity leave        → 5  (On leave)
             6.0: 5.0,   # family care or home    → 5  (On leave)
            14.0: 5.0,   # shared parental leave  → 5  (On leave)
            15.0: 5.0,   # adoption leave         → 5  (On leave)
            # ── Student / training (7) ───────────────────────────────────
             7.0: 7.0,   # full-time student      → 7  (Student / training)
             9.0: 7.0,   # govt training scheme   → 7  (Student / training)
            11.0: 7.0,   # apprenticeship         → 7  (Student / training)
            # ── Inactive (8) ─────────────────────────────────────────────
             8.0: 8.0,   # LT sick or disabled    → 8  (Inactive)
            10.0: 8.0,   # unpaid family business → 8  (Inactive)
            97.0: 8.0,   # doing something else   → 8  (Inactive)
            -1.0: 8.0,   # missing / not stated    → 8  (Inactive)
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
        "cluster":     False,  # split variable only — groups defined in 6_cluster.ipynb; raw column is constant within each group so adds nothing to K-Means
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
    k: v.get("one_hot")
    for k, v in VARIABLES.items()
    if v.get("one_hot") is not None
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

# Variables sourced from xwavedat (looked up by code)
XWAVE_VARS = {k for k, v in VARIABLES.items() if v.get("xwave")}

# Transforms to apply during feature engineering: base_code -> transform name
TRANSFORMS = {k: v["transform"] for k, v in VARIABLES.items() if v.get("transform")}
