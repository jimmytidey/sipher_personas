# data_pipeline/config_paths.py
#
# Single flag that switches the entire pipeline between real and test data.
#
# ┌─────────────────────────────────────────────────────────────────────┐
# │  Flip USE_TEST_DATA = True  to run the full pipeline against the    │
# │  data_test/ folder.  Set it back to False for the real data/ run.   │
# │                                                                     │
# │  In both modes the pipeline uses the real config_variables.py and   │
# │  config_cluster.py — only the I/O folder changes.                   │
# └─────────────────────────────────────────────────────────────────────┘

USE_TEST_DATA = False

# When True, restrict geography-heavy steps to four London boroughs only (fast dry run):
#   Newham, Tower Hamlets, Islington, Hounslow.
# Uses real data/ (not data_test/) unless USE_TEST_DATA is also True.
# Affects: 5_synthetic_population (filters rows); 6_cluster; 7_group_averages;
#          8_label_clusters; 9_generate_portraits (same UNIT_FILTER as step 6).
USE_FOUR_LA_SUBSET = True

# ONS LA codes (2021 LAD) — must match ladcd in admin_geography_mappings.csv
FOUR_LA_CODES: tuple[str, ...] = (
    "E09000025",  # Newham
    "E09000030",  # Tower Hamlets
    "E09000019",  # Islington
    "E09000018",  # Hounslow
)

# Derived value used by every pipeline notebook
DATA_FOLDER = "data_test" if USE_TEST_DATA else "data"

if USE_TEST_DATA:
    print("\n" + "⚠️ " * 30)
    print("  TEST MODE ACTIVE — reading/writing data_test/ (100 rows)")
    print("  Results are NOT representative. Set USE_TEST_DATA = False for a real run.")
    print("⚠️ " * 30 + "\n")

if USE_FOUR_LA_SUBSET:
    _names = "Newham, Tower Hamlets, Islington, Hounslow"
    print("\n" + "🗺️  " * 20)
    print(f"  FOUR-LA SUBSET ACTIVE — {_names} only ({len(FOUR_LA_CODES)} LAs)")
    print("  Set USE_FOUR_LA_SUBSET = False for all London or full UK.")
    print("🗺️  " * 20 + "\n")
