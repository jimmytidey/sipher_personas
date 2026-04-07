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

from __future__ import annotations

import glob
import os
import sys

# Notebook pattern: ``import config_paths`` then ``importlib.reload(config_paths)`` would
# print pipeline banners twice (module body runs on each load). Persist flags outside the
# module so reload does not repeat the same banner in one kernel session.
_BANNER_STATE_KEY = "_archetypes_pipeline_config_paths_banners"


def _banner_flags() -> dict[str, bool]:
    if _BANNER_STATE_KEY not in sys.modules:
        sys.modules[_BANNER_STATE_KEY] = {"test": False, "four_la": False}
    return sys.modules[_BANNER_STATE_KEY]  # type: ignore[return-value]

USE_TEST_DATA = False

# UKHLS main interview waves (newest → oldest). Used to sort waves discovered on disk;
# step 3 backfill also uses this order for look-back priority.
UKHLS_WAVES_ALL: tuple[str, ...] = ("o", "n", "m", "l", "k", "j", "a")
UKHLS_WAVES = ("o",) if USE_TEST_DATA else UKHLS_WAVES_ALL


def list_indresp_waves_in_pickle_dir(pickle_dir: str) -> list[str]:
    """Wave ids that have ``{wave}_indresp_optimized.pkl`` under ``pickle_dir``.

    Sorted newest→oldest using :data:`UKHLS_WAVES_ALL`. Any filename prefix not in
    that tuple sorts after known waves, alphabetically.
    """
    if not os.path.isdir(pickle_dir):
        return []
    pattern = os.path.join(pickle_dir, "*_indresp_optimized.pkl")
    waves: list[str] = []
    for path in glob.glob(pattern):
        base = os.path.basename(path)
        if not base.endswith("_indresp_optimized.pkl"):
            continue
        wave = base[: -len("_indresp_optimized.pkl")]
        if wave:
            waves.append(wave)
    waves = list(dict.fromkeys(waves))
    order = {w: i for i, w in enumerate(UKHLS_WAVES_ALL)}
    unknown_rank = len(UKHLS_WAVES_ALL)
    waves.sort(key=lambda w: (order.get(w, unknown_rank), w))
    return waves

# When True, restrict geography-heavy steps to four London boroughs only (fast dry run):
#   Newham, Tower Hamlets, Islington, Hounslow.
# Uses real data/ (not data_test/) unless USE_TEST_DATA is also True.
# Affects: 6_synthetic_population (filters rows); 7_cluster_local_level; 9_group_averages;
#          10_label_local_level_clusters; 11_label_national_level_clusters; 12_generate_portraits.
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

_flags = _banner_flags()

if USE_TEST_DATA:
    if not _flags["test"]:
        _flags["test"] = True
        print("\n" + "⚠️ " * 30)
        print("  TEST MODE ACTIVE — reading/writing data_test/ (100 rows)")
        print("  Results are NOT representative. Set USE_TEST_DATA = False for a real run.")
        print("⚠️ " * 30 + "\n")
else:
    _flags["test"] = False

if USE_FOUR_LA_SUBSET:
    if not _flags["four_la"]:
        _flags["four_la"] = True
        _names = "Newham, Tower Hamlets, Islington, Hounslow"
        print("\n" + "🗺️  " * 20)
        print(f"  FOUR-LA SUBSET ACTIVE — {_names} only ({len(FOUR_LA_CODES)} LAs)")
        print("  Set USE_FOUR_LA_SUBSET = False for all London or full UK.")
        print("🗺️  " * 20 + "\n")
else:
    _flags["four_la"] = False
