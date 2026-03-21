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

# Derived value used by every pipeline notebook
DATA_FOLDER = "data_test" if USE_TEST_DATA else "data"

if USE_TEST_DATA:
    print("\n" + "⚠️ " * 30)
    print("  TEST MODE ACTIVE — reading/writing data_test/ (100 rows)")
    print("  Results are NOT representative. Set USE_TEST_DATA = False for a real run.")
    print("⚠️ " * 30 + "\n")
