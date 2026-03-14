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

WAVE     = "o"

# ── Number of clusters to aim for ────────────────────────────────────────────
# Used as the K for flat clustering (USE_GROUPED_CLUSTERING = False) and as the
# default K for every employment group (USE_GROUPED_CLUSTERING = True).
# The actual number produced per unit may be lower when a group is too small
# (enforced by MIN_CLUSTER_SIZE in the notebook).
TARGET_K = 10

K_DEFAULT = TARGET_K   # kept for backward-compatibility; don't edit directly

# When True (default), the population is first split by employment status (GROUPS)
# and K-Means is run independently within each group — producing e.g. "Employed 1",
# "Retired 2" etc.
# When False, the entire unit population is clustered together in one pass using
# TARGET_K clusters.
USE_GROUPED_CLUSTERING = True


GROUPS = {
    # Matches jbstat canonical group labels in config_variables.py
    "Employed": {
        "jbstat": ["Employed"],   # paid employment, self-employed, apprenticeship, furlough, laid off
        "k": TARGET_K,
    },
    "Retired": {
        "jbstat": ["Retired"],
        "k": TARGET_K,
    },
    "Unemployed": {
        "jbstat": ["Unemployed"],
        "k": TARGET_K,
    },
    "Student": {
        "jbstat": ["Student"],    # full-time student + govt training
        "k": TARGET_K,
    },
    "On leave": {
        "jbstat": ["On leave"],   # maternity, parental, adoption, family care
        "k": TARGET_K,
    },
    "Inactive": {
        "jbstat": ["Inactive"],   # LT sick/disabled, unpaid family business, other, missing
        "k": TARGET_K,
    },
}
