# ── Regional Cluster Config ───────────────────────────────────────────────────
#
# Defines how to cluster the population.
#
# MAX_TOTAL_CLUSTERS : total cluster budget shared across all employment groups.
#   Each group receives clusters in proportion to its share of the population,
#   so large groups get more tribes than small ones.
#   Actual tribes per group = max(1, round(MAX_TOTAL_CLUSTERS * n_group / n_total))
#   and is further capped by MIN_CLUSTER_SIZE in the notebook.
# ─────────────────────────────────────────────────────────────────────────────

WAVE = "o"

# ── K-Means feature variables ─────────────────────────────────────────────────
# Derived from variables with cluster=True in config_variables_*.py.
# To change which variables are clustered, set "cluster": True/False in the
# relevant theme file (e.g. config_variables_sipher_weighted.py).
try:
    from data_pipeline.config_variables import CLUSTER_VARS
except ModuleNotFoundError:
    from config_variables import CLUSTER_VARS

# ── Total cluster budget ─────────────────────────────────────────────────────
# Shared proportionally across all employment groups.
MAX_TOTAL_CLUSTERS = 50

# When True (default), the population is first split by employment status (GROUPS)
# and K-Means is run independently within each group — producing e.g. "Employed 1",
# "Retired 2" etc.
# When False, the entire unit population is clustered together in one pass using
# MAX_TOTAL_CLUSTERS clusters.
USE_GROUPED_CLUSTERING = True

# ── Grouping variable ─────────────────────────────────────────────────────────
# Base code (without wave prefix) of the OHE variable used to split the population.
GROUP_VAR = "jbstat"

# Ordered list of canonical group names matching the OHE category labels in
# config_variables.py. The last entry with no matching OHE column acts as a
# catch-all for anyone not assigned to a named group.
GROUPS = [
    "Employed",    # paid employment, self-employed, apprenticeship, furlough, laid off
    "Retired",
    "Unemployed",
    "Student",     # full-time student + govt training
    "On leave",    # maternity, parental, adoption, family care
    "Inactive",    # LT sick/disabled, unpaid family business, other, missing
]
