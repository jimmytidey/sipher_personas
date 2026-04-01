# data_pipeline/config_variables.py
#
# Single source of truth for all UKHLS variables used in this pipeline.
# Each entry is a dict with:
#   code        - base variable name (wave prefix e.g. o_ handled by ingestion)
#   label       - human-readable description
#   categorical - True if the variable is categorical, False if continuous
#   categories  - dict mapping raw numeric code (float) -> English label, or None
#   group_labels- (optional) post-recode display labels {canonical_code -> label};
#                 overrides categories in CATEGORY_MAPS when present
#   fill        - imputation strategy: "mode" | "median" | "zero" | None
#   one_hot     - list of category codes (float) to one-hot encode, or None
#   clip        - (optional) upper bound to clip outliers before clustering/viz
#   floor       - (optional) lower bound to clip (e.g. 0 to zero-out negative pay)
#   recode      - (optional) dict of {raw_value -> new_value} applied before use
#   bin_width   - (optional) fixed histogram bin width for visualisation (overrides auto-binning)
#   backfill    - list of values that trigger a look-back through older waves (e.g.
#                 [-9, -7, -2, -1]); NaN always triggers if a list is provided.
#                 Use None or [] to disable backfill for this variable.
#   xwave       - (optional) True if this variable should be sourced from xwavedat.pkl
#                 (looked up by code); xwave vars are never backfilled
#   transform   - (optional) transformation applied during feature engineering, e.g.
#                 "birth_year_to_age"
#
# K-Means inputs: see config_cluster.CLUSTER_VARS (re-exported below as CLUSTER_VARS).
#
# Variable blocks live in theme modules (merged in order below).

import copy

# Notebooks often run with cwd=data_pipeline/ and use `import config_variables` (flat).
# In that case `data_pipeline` is not a package on sys.path — use same-directory imports.
try:
    from data_pipeline import config_cluster
    from data_pipeline.config_variables_demographics import VARIABLES as _VAR_DEMOGRAPHICS
    from data_pipeline.config_variables_digital import VARIABLES as _VAR_DIGITAL
    from data_pipeline.config_variables_derived import VARIABLES as _VAR_DERIVED
    from data_pipeline.config_variables_local_service import VARIABLES as _VAR_LOCAL_SERVICE
    from data_pipeline.config_variables_public_service import VARIABLES as _VAR_PUBLIC_SERVICE
    from data_pipeline.config_variables_transport import VARIABLES as _VAR_TRANSPORT
except ModuleNotFoundError:  # pragma: no cover
    import config_cluster
    from config_variables_demographics import VARIABLES as _VAR_DEMOGRAPHICS
    from config_variables_digital import VARIABLES as _VAR_DIGITAL
    from config_variables_derived import VARIABLES as _VAR_DERIVED
    from config_variables_local_service import VARIABLES as _VAR_LOCAL_SERVICE
    from config_variables_public_service import VARIABLES as _VAR_PUBLIC_SERVICE
    from config_variables_transport import VARIABLES as _VAR_TRANSPORT


def _merge_variable_dicts(*parts):
    """Merge top-level variable code keys; later dicts overwrite earlier on duplicate keys."""
    out = {}
    for part in parts:
        for k, v in part.items():
            out[k] = copy.deepcopy(v)
    return out


VARIABLES = _merge_variable_dicts(
    _VAR_DEMOGRAPHICS,
    _VAR_LOCAL_SERVICE,
    _VAR_PUBLIC_SERVICE,
    _VAR_TRANSPORT,
    _VAR_DIGITAL,
    _VAR_DERIVED,
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

CLUSTER_VARS = list(config_cluster.CLUSTER_VARS)
_unknown = [c for c in CLUSTER_VARS if c not in VARIABLES]
if _unknown:
    raise ValueError(
        f"config_cluster.CLUSTER_VARS has unknown variable codes (not in VARIABLES): {_unknown}"
    )

# Variables shown in the regional cluster summary table (all variables now included)
SUMMARY_VARS = list(VARIABLES.keys())

# Variables to one-hot encode: code -> list of float category codes
# Use pd.get_dummies or equivalent with these column subsets
ONE_HOT_VARS = {
    k: v.get("one_hot")
    for k, v in VARIABLES.items()
    if v.get("one_hot") is not None
}

# Fill strategy lookup: code -> "mode" | "median" | "zero" | None
FILL_STRATEGIES = {k: v["fill"] for k, v in VARIABLES.items()}

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

# Variables sourced from xwavedat (looked up by code)
XWAVE_VARS = {k for k, v in VARIABLES.items() if v.get("xwave")}

# Transforms to apply during feature engineering: base_code -> transform name
TRANSFORMS = {k: v["transform"] for k, v in VARIABLES.items() if v.get("transform")}


def reload_config_variables() -> None:
    """Reload theme modules, ``config_cluster``, LLM vars, and this module.

    Call from Jupyter after editing ``config_variables_*.py`` so changes apply
    without restarting the kernel. Then re-import names from ``config_variables``::

        import config_variables
        config_variables.reload_config_variables()
        from config_variables import VARIABLES, VARIABLE_MAP
    """
    import importlib
    import sys

    _themes = (
        "config_variables_demographics",
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
    for key in ("config_cluster", "data_pipeline.config_cluster"):
        if key in sys.modules:
            importlib.reload(sys.modules[key])
    for key in ("config_variables", "data_pipeline.config_variables"):
        if key in sys.modules:
            importlib.reload(sys.modules[key])
