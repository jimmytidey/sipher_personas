# data_pipeline/config_variables.py
#
# Single source of truth for all UKHLS variables used in this pipeline.
# Each entry is a dict with:
#   code        - base variable name (wave prefix e.g. o_ handled by ingestion)
#   label       - human-readable description
#   categorical - True if the variable is categorical, False if continuous
#   categories  - dict mapping code (float) -> label; use -1.0: "Not provided" for the 3a sentinel
#                 (other negative keys omitted). Real survey code 0 may appear separately. None if N/A.
#   group_labels- (optional) post-recode display labels {canonical_code -> label};
#                 overrides categories in CATEGORY_MAPS when present
#   one_hot     - list of category codes (float) to one-hot encode, or None
#   clip        - (optional) upper bound to clip outliers before clustering/viz
#   floor       - (optional) lower bound to clip (e.g. 0 to zero-out negative pay)
#   recode      - (optional) dict of {raw_value -> new_value} applied before use.
#                 Do not map UKHLS negative codes here — 3a backfill remaps them to -1.
#   bin_width   - (optional) fixed histogram bin width for visualisation (overrides auto-binning)
#   backfill    - list of values that trigger a look-back through older waves (e.g.
#                 [-9, -7, -2, -1]); NaN always triggers if a list is provided.
#                 Use None or [] to disable backfill for this variable.
#   file        - (optional) source file: "xwave" for xwavedat.pkl, "hhresp" for
#                 household response; omit (or "indresp") for individual response.
#                 xwave vars are never backfilled.
#   transform   - (optional) transformation applied during feature engineering, e.g.
#                 "birth_year_to_age"
#
# K-Means inputs: variables with cluster=True in their definition (re-exported below as CLUSTER_VARS).
#
# Variable blocks live in theme modules (merged in order below).

import copy
from collections.abc import Collection

# Repo-root ``data/`` directory name (notebooks use ``f"../{DATA_FOLDER}/…"`` from data_pipeline/).
DATA_FOLDER = "data"

# Notebooks often run with cwd=data_pipeline/ and use `import config_variables` (flat).
# In that case `data_pipeline` is not a package on sys.path — use same-directory imports.
try:
    from data_pipeline.config.config_variables_sipher_weighted import VARIABLES as _VAR_DEMOGRAPHICS
    from data_pipeline.config.config_variables_economic import VARIABLES as _VAR_ECONOMIC
    from data_pipeline.config.config_variables_digital import VARIABLES as _VAR_DIGITAL
    from data_pipeline.config.config_variables_derived import VARIABLES as _VAR_DERIVED
    from data_pipeline.config.config_variables_local_service import VARIABLES as _VAR_LOCAL_SERVICE
    from data_pipeline.config.config_variables_public_service import VARIABLES as _VAR_PUBLIC_SERVICE
    from data_pipeline.config.config_variables_transport import VARIABLES as _VAR_TRANSPORT
except ModuleNotFoundError:  # pragma: no cover
    from config.config_variables_sipher_weighted import VARIABLES as _VAR_DEMOGRAPHICS
    from config.config_variables_economic import VARIABLES as _VAR_ECONOMIC
    from config.config_variables_digital import VARIABLES as _VAR_DIGITAL
    from config.config_variables_derived import VARIABLES as _VAR_DERIVED
    from config.config_variables_local_service import VARIABLES as _VAR_LOCAL_SERVICE
    from config.config_variables_public_service import VARIABLES as _VAR_PUBLIC_SERVICE
    from config.config_variables_transport import VARIABLES as _VAR_TRANSPORT


def _merge_variable_dicts(*parts):
    """Merge top-level variable code keys; later dicts overwrite earlier on duplicate keys."""
    out = {}
    for part in parts:
        for k, v in part.items():
            out[k] = copy.deepcopy(v)
    return out


VARIABLES = _merge_variable_dicts(
    _VAR_DEMOGRAPHICS,
    #_VAR_ECONOMIC,
    #_VAR_LOCAL_SERVICE,
    #_VAR_PUBLIC_SERVICE,
    #_VAR_TRANSPORT,
    #_VAR_DIGITAL,
    #_VAR_DERIVED,
)

# -----------------------------------------------------------------------------
# Convenience accessors derived from VARIABLES (single source of truth)
# -----------------------------------------------------------------------------

# code -> label  (mirrors old VARIABLE_MAP)
VARIABLE_MAP = {k: v["label"] for k, v in VARIABLES.items()}

# code -> category dict used for display (group_labels takes precedence over
# categories when present — allows raw categories to document all codes while
# group_labels reflects post-recode canonical values)
CATEGORY_MAPS = {
    k: v.get("group_labels") or v["categories"]
    for k, v in VARIABLES.items()
    if v["categorical"] and (v.get("group_labels") or v["categories"]) is not None
}

# Sets of codes by type
CATEGORICAL_VARS = {k for k, v in VARIABLES.items() if v["categorical"]}
CONTINUOUS_VARS  = {k for k, v in VARIABLES.items() if not v["categorical"]}

CLUSTER_VARS = [k for k, v in VARIABLES.items() if v.get("cluster")]

# UKHLS wave prefix for engineered columns (must match 3a primary + 4a input pickle).
# Wave k is the SIPHER-aligned cohort (all SIPHER pidps with a k-wave interview); o is newer but smaller.
WAVE = "k"

# Step 12 group baselines: jbstat one-hot column names (last catch-all uses col is None).
GROUPS = [
    "Employed",
    "Retired",
    "Unemployed",
    "Student",
    "On leave",
    "Inactive",
]

# Variables shown in the regional cluster summary table (all variables now included)
SUMMARY_VARS = list(VARIABLES.keys())

# Variables to one-hot encode: code -> True (all category codes) or list of codes.
# Omitted when ``one_hot`` is missing, ``False``, or empty — those variables skip OHE.
ONE_HOT_VARS = {k: v["one_hot"] for k, v in VARIABLES.items() if v.get("one_hot")}


def expected_ohe_column_names(wave: str, base: str) -> list[str]:
    """
    Names of binary columns created in 4a for one OHE variable (category dummies + not_answered).

    Columns use the _eng infix — e.g. o_racel_dv_eng_1, o_racel_dv_eng_not_answered —
    reflecting that OHE is always derived from the feature-engineered (recoded) values.

    Must stay aligned with 4a_feature_eng_ukhls.ipynb (OHE sub-step in the numbered list).
    """
    one_hot_spec = ONE_HOT_VARS[base]
    var_def = VARIABLES[base]
    if one_hot_spec is True:
        keys_src = var_def.get("group_labels") or var_def["categories"]
        codes = list(keys_src.keys())
    else:
        codes = list(one_hot_spec)

    cols = [f"{wave}_{base}_eng_{int(code)}" for code in codes]
    cols.append(f"{wave}_{base}_eng_not_answered")
    return cols


# Variables that receive any scalar feature engineering in step 4a (transform /
# recode / floor / clip).  Downstream steps use {wave}_{base}_eng for these.
# Populated after RECODE_MAPS etc. are defined (see bottom of file).
_ENG_VARS: set[str] = set()  # filled in below


def expected_cluster_feature_columns(wave: str) -> list[str]:
    """
    Ordered column names passed to K-Means (and normalise.fit).

    For OHE variables, uses the _eng dummy columns (e.g. o_racel_dv_eng_1).
    For scalar variables that were recoded / transformed / clipped in 4a,
    uses the _eng column (e.g. o_doby_dv_eng, o_hiqual_dv_eng).
    For unmodified scalar variables, uses the raw column (e.g. o_scsf1).
    """
    out: list[str] = []
    for base in CLUSTER_VARS:
        if base in ONE_HOT_VARS:
            out.extend(expected_ohe_column_names(wave, base))
        elif base in _ENG_VARS:
            out.append(f"{wave}_{base}_eng")
        else:
            out.append(f"{wave}_{base}")
    return out

# Upper-clip values for outlier-prone continuous variables: code -> numeric upper bound
CLIP_VALUES = {k: v["clip"] for k, v in VARIABLES.items() if v.get("clip") is not None}

# Lower-floor values: code -> numeric lower bound (values below this are set to floor)
FLOOR_VALUES = {k: v["floor"] for k, v in VARIABLES.items() if v.get("floor") is not None}

# Fixed histogram bin widths for visualisation: code -> bin width
BIN_WIDTHS = {k: v["bin_width"] for k, v in VARIABLES.items() if v.get("bin_width") is not None}

# Value recoding: code -> {old_value: new_value} applied before clustering/viz
RECODE_MAPS = {k: v["recode"] for k, v in VARIABLES.items() if v.get("recode") is not None}

# Disability one-hot label mapping (used when expanding o_disdif1..96)
DISABILITY_LABELS = {
    "1":  "mobility",       "2":  "visual",        "3":  "hearing",
    "4":  "learning",       "5":  "mental_health",  "6":  "dexterity",
    "7":  "stamina",        "8":  "memory",         "9":  "behavioral",
    "10": "progressive",    "11": "other",          "96": "other",
}

# Variables grouped by source file
XWAVE_VARS  = {k for k, v in VARIABLES.items() if v.get("file") == "xwave"}
HHRESP_VARS = {k for k, v in VARIABLES.items() if v.get("file") == "hhresp"}

# Transforms to apply during feature engineering: base_code -> transform name
TRANSFORMS = {k: v["transform"] for k, v in VARIABLES.items() if v.get("transform")}

# Populate _ENG_VARS now that RECODE_MAPS / TRANSFORMS / FLOOR_VALUES / CLIP_VALUES exist.
# Any variable whose scalar value is modified in step 4a gets a {wave}_{base}_eng column.
_ENG_VARS = (
    set(RECODE_MAPS.keys())
    | set(TRANSFORMS.keys())
    | set(FLOOR_VALUES.keys())
    | set(CLIP_VALUES.keys())
)


def preferred_summary_column(wave: str, base: str, columns: Collection[str]) -> str | None:
    """
    DataFrame column to use for tribe / persona summaries (e.g. ``build_dna_row``).

    Step 4a stores transformed or recoded scalars in ``{wave}_{base}_eng`` (age from
    ``birth_year_to_age``, recoded jbstat, etc.). The raw ``{wave}_{base}`` column
    may still hold pre-engineering values (e.g. year of birth for ``doby_dv``).
    Feature-engineered tables are written under ``data/4_feature_eng/{wave}_feature_eng.pkl``.
    """
    colset = set(columns)
    eng = f"{wave}_{base}_eng"
    raw = f"{wave}_{base}"
    if base in _ENG_VARS and eng in colset:
        return eng
    if raw in colset:
        return raw
    return None


def reload_config_variables() -> None:
    """Reload theme modules, LLM vars, and this module.

    Call from Jupyter after editing ``config_variables_*.py`` so changes apply
    without restarting the kernel. Then re-import names from ``config_variables``::

        import config_variables
        config_variables.reload_config_variables()
        from config_variables import VARIABLES, VARIABLE_MAP
    """
    import importlib
    import sys

    # Renamed/removed theme modules can linger in sys.modules; reload would raise
    # ModuleNotFoundError (spec not found) after the file is gone.
    for _stale in (
        "config_variables_demographics",
        "data_pipeline.config_variables_demographics",
    ):
        sys.modules.pop(_stale, None)

    _themes = (
        "config_variables_sipher_weighted",
        "config_variables_economic",
        "config_variables_local_service",
        "config_variables_public_service",
        "config_variables_transport",
        "config_variables_digital",
        "config_variables_derived",
    )
    for base in _themes:
        for key in (base, f"data_pipeline.{base}"):
            if key in sys.modules:
                importlib.reload(sys.modules[key])
    for key in ("config_variables", "data_pipeline.config_variables"):
        if key in sys.modules:
            importlib.reload(sys.modules[key])
