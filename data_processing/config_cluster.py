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
    "Employed": {
        "jbstat": ["Employed"],
        "k": 3,
    },
    "Self-employed": {
        "jbstat": ["Self-employed"],
        "k": 3,
    },
    "Retired": {
        "jbstat": ["Retired"],
        "k": 3,
    },
    "Unemployed": {
        "jbstat": ["Unemployed"],
        "k": 3,
    },
    "Student": {
        "jbstat": ["Full-time student"],
        "k": 3, 
    },
    "Other": {
        "jbstat": ["Maternity leave", "Family care", "LT sick/disabled",
                   "Govt scheme", "Unpaid family work", "Other"],
        "k": 3,
    },
}
