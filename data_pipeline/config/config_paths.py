# data_pipeline/config_paths.py
#
# Path and scope configuration shared across pipeline notebooks.

# Root data directory (notebooks resolve paths as f"../{DATA_FOLDER}/…").
DATA_FOLDER = "data"

# Set True to restrict Phase 2 output to four test LAs (FOUR_LA_CODES below).
# Clustering itself is always national regardless of this flag.
USE_FOUR_LA_SUBSET = False

# Four representative London boroughs used when USE_FOUR_LA_SUBSET is True.
FOUR_LA_CODES = frozenset([
    "E09000001",  # City of London
    "E09000002",  # Barking and Dagenham
    "E09000003",  # Barnet
    "E09000004",  # Bexley
])
