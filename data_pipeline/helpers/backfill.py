# helpers/backfill.py
#
# UKHLS interview-wave ordering and indresp pickle discovery for the pickle + backfill
# pipeline (steps 2_pickle_ukhls_waves and 3a_backfill_ukhls_waves).

from __future__ import annotations

import glob
import os

# Main interview waves, newest → oldest. Step 2 uses this order for which waves to ingest;
# step 3a uses it to sort pickles found on disk and for look-back priority among backups.
UKHLS_WAVES_ALL: tuple[str, ...] = ("o", "n", "m", "l", "k", "j", "a")
UKHLS_WAVES = UKHLS_WAVES_ALL


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
