# data_pipeline/config_cluster.py
#
# Clustering configuration shared across pipeline notebooks.

try:
    from data_pipeline.config_variables import WAVE, GROUPS
except ModuleNotFoundError:
    from config_variables import WAVE, GROUPS

# Fixed number of K-Means clusters to fit.
N_CLUSTERS = 10

# ── Local-level clustering ─────────────────────────────────────────────────────
# Number of clusters to fit per Local Authority.
N_CLUSTERS_LOCAL = 5

# Test mode: when True, only process the LAs listed in TEST_LA_CODES.
# Set to False (or None) to run all LAs.
TEST_MODE = True
TEST_LA_CODES = [
    "E09000030",  # Tower Hamlets  (includes Bethnal Green ward)
    "E09000019",  # Islington
    "E09000018",  # Hounslow
    "E09000025",  # Newham
    "E06000047",  # County Durham
    "E06000009",  # Blackpool
]

# ── Hierarchical clustering ────────────────────────────────────────────────────
# When set to a column base name (without wave prefix), each LA is first split by
# the unique values of that column and N_CLUSTERS_LOCAL clusters are fitted
# independently within each group.  The summary CSV will contain a `group` column
# identifying which group each cluster row belongs to.
# Set to False to disable and cluster the entire LA population as a single group.
HIERARCHICAL_CLUSTER = "jbstat_eng"
