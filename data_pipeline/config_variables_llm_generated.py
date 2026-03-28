# data_pipeline/config_variables_llm_generated.py
#
# Curated UKHLS variable set (~20 substantive fields + pidp) for themes:
#   digital skills / internet use, migration (first- and second-generation proxies),
#   and use of public / advice services.
#
# Same schema as config_variables.py. Base `code` names match indresp columns
# without the wave prefix (e.g. o_netpusenew → netpusenew).
#
# Merged into config_variables.VARIABLES after theme + pipeline-only keys; duplicate
# keys already present take precedence.
#
# Import from config_variables for VARIABLE_MAP, CATEGORY_MAPS, etc.; this module
# only supplies LLM_GENERATED_VARIABLES.

from __future__ import annotations

LLM_GENERATED_VARIABLES = {

    "pidp": {
        "code":        "pidp",
        "label":       "Unique Person ID (anchor for all joins)",
        "categorical": False,
        "categories":  None,
        "fill":        None,
        "one_hot":     None,
        "backfill":    None,
    },

    # -------------------------------------------------------------------------
    # Digital skills & technology use
    # -------------------------------------------------------------------------
    "netpusenew": {
        "code":        "netpusenew",
        "label":       "Internet use frequency (general)",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
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
        "fill":        "mode",
        "one_hot":     None,
    },
    "netuse": {
        "code":        "netuse",
        "label":       "Regularly uses the internet",
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
    "onlinebank": {
        "code":        "onlinebank",
        "label":       "Frequency: online banking",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            1.0: "Every day",
            2.0: "Several times a week",
            3.0: "Several times a month",
            4.0: "Once a month",
            5.0: "Less than once a month",
            6.0: "Never",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "onlinebuy": {
        "code":        "onlinebuy",
        "label":       "Frequency: online buying",
        "categorical": True,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  {
            -9.0: "Missing",
            -8.0: "Inapplicable",
            -7.0: "Proxy",
            -2.0: "Refusal",
            -1.0: "Don't know",
            1.0: "Every day",
            2.0: "Several times a week",
            3.0: "Several times a month",
            4.0: "Once a month",
            5.0: "Less than once a month",
            6.0: "Never",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "smartmob": {
        "code":        "smartmob",
        "label":       "Has a smartphone",
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
    "laptop": {
        "code":        "laptop",
        "label":       "Access to a laptop (mobile technology module)",
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

    # -------------------------------------------------------------------------
    # Migration & citizenship (first-generation: bornuk_dv, yr2uk, reasons;
    # second-generation proxies: parents’ country of birth)
    # bornuk_dv is xwavedat (derived); raw ukborn remains in feature_eng for immigrant generation
    # -------------------------------------------------------------------------
    "bornuk_dv": {
        "code":        "bornuk_dv",
        "label":       "Born in UK (derived)",
        "categorical": True,
        "xwave":       True,
        "backfill":    None,
        "categories":  {
            -9.0: "Missing",
            1.0: "Born in UK",
            2.0: "Not born in UK",
        },
        "fill":        "mode",
        "one_hot":     None,
    },
    "yr2uk4": {
        "code":        "yr2uk4",
        "label":       "Year first came to live in Britain (first-generation migrants)",
        "categorical": False,
        "backfill":    [-9, -8, -2, -1],
        "categories":  None,
        "fill":        "median",
        "one_hot":     None,
        "floor":       1900,
        "clip":        2030,
    },
    "plbornc": {
        "code":        "plbornc",
        "label":       "Country of birth (numeric code — high cardinality)",
        "categorical": False,
        "backfill":    [-9, -8, -2, -1],
        "categories":  None,
        "fill":        "median",
        "one_hot":     None,
    },
    "citzn1": {
        "code":        "citzn1",
        "label":       "Citizenship: UK citizen (mentioned)",
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
    "citzn2": {
        "code":        "citzn2",
        "label":       "Citizenship: citizen of country of birth (mentioned)",
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
    "citzn3": {
        "code":        "citzn3",
        "label":       "Citizenship: citizen of another country (mentioned)",
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
    "pacob": {
        "code":        "pacob",
        "label":       "Country father born in (numeric code — second-gen / heritage)",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  None,
        "fill":        "median",
        "one_hot":     None,
    },
    "macob": {
        "code":        "macob",
        "label":       "Country mother born in (numeric code — second-gen / heritage)",
        "categorical": False,
        "backfill":    [-9, -8, -7, -2, -1],
        "categories":  None,
        "fill":        "median",
        "one_hot":     None,
    },
    "mreason1": {
        "code":        "mreason1",
        "label":       "Reason for migration: for work (mentioned)",
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
    # Public & advice services (health + benefits-related)
    # -------------------------------------------------------------------------
    "servuse1": {
        "code":        "servuse1",
        "label":       "Service use (12 m): local GP",
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
    "servuse2": {
        "code":        "servuse2",
        "label":       "Service use (12 m): local hospital",
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
        "label":       "Service use (12 m): advice services (e.g. benefits)",
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
    "hl2gp": {
        "code":        "hl2gp",
        "label":       "GP visits in last 12 months (banded count)",
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
}

# Backward-compatible alias (prefer importing from config_variables)
VARIABLES = LLM_GENERATED_VARIABLES
