# ── Regional Cluster Config ───────────────────────────────────────────────────
#
# Defines how to cluster within each employment-status group.
#
# Each group entry:
#   "jbstat":    list of jbstat category labels (from config_variables CATEGORY_MAPS)
#   "k":         number of GMM components (set to 1 to keep as a single tribe)
#   "variables": (optional) list of CLUSTER_VAR base codes to use for this group.
#                Omit to use all CLUSTER_VARS defined in config_variables.py.
# ─────────────────────────────────────────────────────────────────────────────

WAVE      = "o"
K_DEFAULT = 2   # fallback K if a group entry has no "k"

GROUPS = {
    # Matches jbstat canonical group labels in config_variables.py
    "Employed": {
        "jbstat": ["Employed"],   # paid employment, self-employed, apprenticeship, furlough, laid off
        "k": 3,
    },
    "Retired": {
        "jbstat": ["Retired"],
        "k": 3,
    },
    "Unemployed": {
        "jbstat": ["Unemployed"],
        "k": 2,
    },
    "Student": {
        "jbstat": ["Student"],    # full-time student + govt training
        "k": 2,
    },
    "On leave": {
        "jbstat": ["On leave"],   # maternity, parental, adoption, family care
        "k": 2,
    },
    "Inactive": {
        "jbstat": ["Inactive"],   # LT sick/disabled, unpaid family business, other, missing
        "k": 2,
    },
}
