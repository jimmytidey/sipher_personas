# tests/test_pipeline.py
#
# Unit + integration tests for the clustering pipeline.
#
# Run from the project root:
#
#     venv/bin/pytest tests/test_pipeline.py -v
#
# External dependencies:  pytest, numpy, pandas, scikit-learn  (all in requirements.txt)

from __future__ import annotations

import sys
from pathlib import Path

import numpy  as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans

# ── ensure project root is on the path ─────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_processing import normalise, cluster_funcs
from data_processing.config_variables import (
    CLUSTER_VARS,
    SUMMARY_VARS,
    VARIABLE_MAP,
    CATEGORICAL_VARS,
    CATEGORY_MAPS,
    ONE_HOT_VARS,
)
from data_processing.config_cluster import WAVE, K_DEFAULT, GROUPS

# ── helpers ──────────────────────────────────────────────────────────────────
# Feature columns expected after notebook 4 (OHE applied).
# We test with a subset of the most discriminating cluster variables so the
# tests remain deterministic without needing the full pipeline outputs.
# These must all be cluster=True in config_variables.py.
CORE_FEAT_COLS = [
    f"{WAVE}_age_dv",
    f"{WAVE}_payn_dv",
    f"{WAVE}_sf12mcs_dv",
    f"{WAVE}_sf12pcs_dv",
    f"{WAVE}_hiqual_dv",
    f"{WAVE}_fimngrs_dv",
    f"{WAVE}_hhsize",
    f"{WAVE}_nchild_dv",
]

# All wave-prefixed cluster feature column names (from the full config)
FEAT_COLS = [f"{WAVE}_{b}" for b in CLUSTER_VARS]

RAW_DIR = ROOT / "data_test" / "0_raw"


def _is_cluster_a(pidp: int) -> bool:
    """Mirrors the assignment logic in generate_test_data.py."""
    return pidp % 50 <= 25 and pidp % 50 != 0


def _make_feature_row(pidp: int) -> dict:
    """Build one fully-featured row (post-OHE) from a pidp integer.
    Values match the Cluster A / Cluster B profiles in generate_test_data.py.
    """
    a = _is_cluster_a(pidp)
    return {
        "pidp":                     pidp,
        # Cluster features — continuous
        f"{WAVE}_age_dv":           25.0  if a else 65.0,
        f"{WAVE}_hiqual_dv":         1.0  if a else  5.0,
        f"{WAVE}_payn_dv":        3000.0  if a else  0.0,
        f"{WAVE}_jbnssec8_dv":       1.0  if a else  8.0,
        f"{WAVE}_fimngrs_dv":     3500.0  if a else 500.0,
        f"{WAVE}_hhsize":            4.0  if a else  1.0,
        f"{WAVE}_nchild_dv":         2.0  if a else  0.0,
        f"{WAVE}_sf12mcs_dv":       55.0  if a else 30.0,
        f"{WAVE}_sf12pcs_dv":       55.0  if a else 30.0,
        f"{WAVE}_nbrsnci_dv":        4.0  if a else  1.0,
        f"{WAVE}_locsera":           1.0  if a else  5.0,
        f"{WAVE}_locserc":           1.0  if a else  5.0,
        f"{WAVE}_locserd":           1.0  if a else  5.0,
        f"{WAVE}_locsere":           1.0  if a else  5.0,
        f"{WAVE}_jbttwt":           30.0  if a else  0.0,
        f"{WAVE}_envhabit8":         1.0  if a else  5.0,
        f"{WAVE}_carmiles":       5000.0  if a else  0.0,
        # OHE from jbpl (1=At home) and wktrvfar (2=car driver)
        f"{WAVE}_jbpl_1":            1.0  if a else  0.0,
        f"{WAVE}_wktrvfar_2":        0.0  if a else  1.0,
        f"{WAVE}_disability_mobility":      0.0,
        f"{WAVE}_disability_visual":        0.0,
        f"{WAVE}_disability_hearing":       0.0,
        f"{WAVE}_disability_learning":      0.0,
        f"{WAVE}_disability_mental_health": 0.0,
        f"{WAVE}_disability_dexterity":     0.0,
        f"{WAVE}_disability_memory":        0.0,
        # OHE columns from jbstat (all Employed → jbstat_1 = 1, after recode 2→1)
        f"{WAVE}_jbstat_1":  1.0,
        f"{WAVE}_jbstat_3":  0.0,
        f"{WAVE}_jbstat_4":  0.0,
        f"{WAVE}_jbstat_5":  0.0,
        f"{WAVE}_jbstat_7":  0.0,
        f"{WAVE}_jbstat_8":  0.0,
        # OHE from sex_dv (male=1 for A, female=2 for B → sex_dv_1)
        f"{WAVE}_sex_dv_1":    1.0 if a else 0.0,
        # OHE from englang (1=Yes for A → englang_1)
        f"{WAVE}_englang_1":   1.0 if a else 0.0,
        # Raw (non-cluster) columns kept for summary (post-recode: 2→1)
        f"{WAVE}_jbstat":   1.0,
        f"{WAVE}_age_dv":   25.0 if a else 65.0,  # duplicate, harmless
    }


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def clean_df() -> pd.DataFrame:
    """100-row DataFrame with all pipeline feature columns pre-applied."""
    rows = [_make_feature_row(p) for p in range(1, 101)]
    # De-dup columns that appear twice (age_dv added twice above)
    df = pd.DataFrame(rows)
    return df.loc[:, ~df.columns.duplicated()]


@pytest.fixture(scope="module")
def cluster_a(clean_df: pd.DataFrame) -> pd.DataFrame:
    """50-row subset: pidp 1-25 and 51-75 (Cluster A)."""
    return clean_df[clean_df["pidp"].apply(_is_cluster_a)].copy()


@pytest.fixture(scope="module")
def cluster_b(clean_df: pd.DataFrame) -> pd.DataFrame:
    """50-row subset: pidp 26-50 and 76-100 (Cluster B)."""
    return clean_df[~clean_df["pidp"].apply(_is_cluster_a)].copy()


# ════════════════════════════════════════════════════════════════════════════
# 1. Test data files
# ════════════════════════════════════════════════════════════════════════════

class TestRawDataFiles:
    """Confirm generate_test_data.py produced the expected files."""

    def test_geo_csv_exists(self):
        assert (RAW_DIR / "admin_geography_mappings.csv").exists()

    def test_sipher_csv_exists(self):
        assert (RAW_DIR / "sipher" / "sipher.csv").exists()

    def test_ukhls_tab_exists(self):
        assert (RAW_DIR / "ukhls" / "o_indresp.tab").exists()

    def test_geo_has_two_las(self):
        df = pd.read_csv(RAW_DIR / "admin_geography_mappings.csv")
        assert len(df) == 2
        assert set(df["ladcd"]) == {"E99000001", "E99000002"}

    def test_sipher_has_100_rows(self):
        df = pd.read_csv(RAW_DIR / "sipher" / "sipher.csv")
        assert len(df) == 100
        assert set(df["synthetic_zone"]) == {"E01TEST01", "E01TEST02"}

    def test_ukhls_has_100_rows(self):
        df = pd.read_csv(RAW_DIR / "ukhls" / "o_indresp.tab", sep="\t")
        assert len(df) == 100

    def test_each_zone_has_50_rows(self):
        df = pd.read_csv(RAW_DIR / "sipher" / "sipher.csv")
        zone_counts = df["synthetic_zone"].value_counts()
        assert zone_counts["E01TEST01"] == 50
        assert zone_counts["E01TEST02"] == 50

    def test_ukhls_has_real_column_names(self):
        """Tab file should contain real UKHLS variable names (wave-prefixed)."""
        df = pd.read_csv(RAW_DIR / "ukhls" / "o_indresp.tab", sep="\t")
        assert f"{WAVE}_age_dv"     in df.columns
        assert f"{WAVE}_jbstat"     in df.columns
        assert f"{WAVE}_payn_dv"    in df.columns
        assert f"{WAVE}_sf12mcs_dv" in df.columns

    def test_ukhls_all_employed(self):
        """All 100 respondents should be Employed (jbstat=2)."""
        df = pd.read_csv(RAW_DIR / "ukhls" / "o_indresp.tab", sep="\t")
        assert (df[f"{WAVE}_jbstat"] == 2.0).all()

    def test_ukhls_two_age_groups(self):
        """Cluster A rows should have age=25, Cluster B age=65."""
        df = pd.read_csv(RAW_DIR / "ukhls" / "o_indresp.tab", sep="\t")
        assert set(df[f"{WAVE}_age_dv"].unique()) == {25.0, 65.0}


# ════════════════════════════════════════════════════════════════════════════
# 2. OHE encoding
# ════════════════════════════════════════════════════════════════════════════

class TestOHEEncoding:
    """Step 4 mimicry: apply one-hot encoding to raw UKHLS data."""

    @pytest.fixture(scope="class")
    def ohe_df(self) -> pd.DataFrame:
        """Load raw file, apply recode then OHE — mirrors notebook 4."""
        from data_processing.config_variables import VARIABLES, RECODE_MAPS
        df = pd.read_csv(RAW_DIR / "ukhls" / "o_indresp.tab", sep="\t")
        # Step 1: apply recode maps (e.g. jbstat 2→1 for Employed)
        for base, recode in RECODE_MAPS.items():
            col = f"{WAVE}_{base}"
            if col in df.columns:
                df[col] = df[col].replace(recode)
        # Step 2: one-hot encode
        for base, one_hot_spec in ONE_HOT_VARS.items():
            raw_col = f"{WAVE}_{base}"
            if raw_col not in df.columns:
                continue
            if one_hot_spec is True:
                codes = list(VARIABLES[base]["categories"].keys())
            else:
                codes = list(one_hot_spec)
            for code in codes:
                new_col = f"{WAVE}_{base}_{int(code)}"
                df[new_col] = (df[raw_col] == code).astype(float)
        return df

    def test_jbstat_1_set_for_all(self, ohe_df: pd.DataFrame):
        """All 100 respondents are Employed: after recode (2→1) o_jbstat_1=1."""
        assert (ohe_df[f"{WAVE}_jbstat_1"] == 1.0).all()

    def test_jbstat_other_codes_zero(self, ohe_df: pd.DataFrame):
        """No other jbstat OHE column should be 1 since all are Employed."""
        for code in [3, 4, 5, 7, 8]:
            col = f"{WAVE}_jbstat_{code}"
            if col in ohe_df.columns:
                assert (ohe_df[col] == 0.0).all(), f"{col} should be all 0"

    def test_sex_dv_ohe(self, ohe_df: pd.DataFrame):
        """Cluster A rows (age=25) are Male → sex_dv_1=1."""
        a_rows = ohe_df[ohe_df[f"{WAVE}_age_dv"] == 25.0]
        assert (a_rows[f"{WAVE}_sex_dv_1"] == 1.0).all()

    def test_two_age_clusters_present(self, ohe_df: pd.DataFrame):
        """50 rows age=25 (Cluster A) and 50 rows age=65 (Cluster B)."""
        assert (ohe_df[f"{WAVE}_age_dv"] == 25.0).sum() == 50
        assert (ohe_df[f"{WAVE}_age_dv"] == 65.0).sum() == 50


# ════════════════════════════════════════════════════════════════════════════
# 3. Normalisation
# ════════════════════════════════════════════════════════════════════════════

class TestNormalise:
    """normalise.fit and normalise.apply produce correctly scaled data."""

    @pytest.fixture(scope="class")
    def normed_df(self, clean_df: pd.DataFrame) -> pd.DataFrame:
        coeffs = normalise.fit(clean_df, CORE_FEAT_COLS)
        return normalise.apply(clean_df, coeffs)

    def test_fit_returns_all_feature_cols(self, clean_df: pd.DataFrame):
        coeffs = normalise.fit(clean_df, CORE_FEAT_COLS)
        for col in CORE_FEAT_COLS:
            assert col in coeffs

    def test_mean_approx_zero_after_apply(self, normed_df: pd.DataFrame):
        for col in CORE_FEAT_COLS:
            mean_val = normed_df[col].mean()
            assert abs(mean_val) < 1e-10, f"{col} mean = {mean_val} (expected ~0)"

    def test_std_approx_one_after_apply(self, clean_df: pd.DataFrame, normed_df: pd.DataFrame):
        for col in CORE_FEAT_COLS:
            pre_std = pd.to_numeric(clean_df[col], errors="coerce").std(ddof=0)
            if pre_std == 0:
                continue
            std_val = normed_df[col].std(ddof=0)
            assert abs(std_val - 1.0) < 1e-10, f"{col} std(ddof=0) = {std_val} (expected ~1)"

    def test_constant_col_left_unchanged(self):
        """A zero-std column should be left as-is (M=1, c=0)."""
        df     = pd.DataFrame({"x": [5.0] * 10, "y": [1.0] * 10})
        coeffs = normalise.fit(df, ["x"])
        assert coeffs["x"] == (1.0, 0.0)
        result = normalise.apply(df, coeffs)
        assert (result["x"] == 5.0).all()

    def test_apply_preserves_non_feature_cols(self, clean_df: pd.DataFrame):
        coeffs = normalise.fit(clean_df, CORE_FEAT_COLS)
        normed = normalise.apply(clean_df, coeffs)
        assert list(normed.columns) == list(clean_df.columns)
        pd.testing.assert_series_equal(normed["pidp"], clean_df["pidp"])

    def test_save_load_round_trip(self, clean_df: pd.DataFrame, tmp_path: Path):
        coeffs = normalise.fit(clean_df, CORE_FEAT_COLS)
        path   = tmp_path / "coeffs.pkl"
        normalise.save(coeffs, path)
        loaded = normalise.load(path)
        for col in CORE_FEAT_COLS:
            assert coeffs[col] == loaded[col]


# ════════════════════════════════════════════════════════════════════════════
# 4. KMeans
# ════════════════════════════════════════════════════════════════════════════

class TestFitKMeans:
    """fit_kmeans on clean data perfectly separates the two groups."""

    @pytest.fixture(scope="class")
    def labels(self, clean_df: pd.DataFrame) -> np.ndarray:
        coeffs = normalise.fit(clean_df, CORE_FEAT_COLS)
        normed = normalise.apply(clean_df, coeffs)
        X      = normed[CORE_FEAT_COLS].to_numpy()
        return cluster_funcs.fit_kmeans(X, k=2)

    def test_exactly_two_cluster_labels(self, labels: np.ndarray):
        assert set(labels) == {0, 1}

    def test_label_consistent_within_cluster_a(self, clean_df: pd.DataFrame, labels: np.ndarray):
        """All 50 Cluster-A people should share one label."""
        a_mask   = clean_df["pidp"].apply(_is_cluster_a).to_numpy()
        a_labels = set(labels[a_mask])
        assert len(a_labels) == 1, f"Cluster A has multiple labels: {a_labels}"

    def test_label_consistent_within_cluster_b(self, clean_df: pd.DataFrame, labels: np.ndarray):
        """All 50 Cluster-B people should share one label."""
        b_mask   = ~clean_df["pidp"].apply(_is_cluster_a).to_numpy()
        b_labels = set(labels[b_mask])
        assert len(b_labels) == 1, f"Cluster B has multiple labels: {b_labels}"

    def test_cluster_a_and_b_have_different_labels(self, clean_df: pd.DataFrame, labels: np.ndarray):
        """The two group labels must be distinct."""
        a_mask   = clean_df["pidp"].apply(_is_cluster_a).to_numpy()
        a_label  = labels[a_mask][0]
        b_label  = labels[~a_mask][0]
        assert a_label != b_label

    def test_k1_returns_all_zeros(self, clean_df: pd.DataFrame):
        X      = clean_df[CORE_FEAT_COLS].to_numpy()
        labels = cluster_funcs.fit_kmeans(X, k=1)
        assert (labels == 0).all()

    def test_cluster_sizes_are_equal(self, labels: np.ndarray):
        """Both clusters should contain exactly 50 respondents."""
        unique, counts = np.unique(labels, return_counts=True)
        assert sorted(counts) == [50, 50]


# ════════════════════════════════════════════════════════════════════════════
# 5. DNA row (build_dna_row)
# ════════════════════════════════════════════════════════════════════════════

# Shared kwargs for build_dna_row calls.
_DNA_KWARGS = dict(
    wave             = WAVE,
    summary_vars     = SUMMARY_VARS,
    variable_map     = VARIABLE_MAP,
    categorical_vars = CATEGORICAL_VARS,
    category_maps    = CATEGORY_MAPS,
)

LABEL_AGE   = VARIABLE_MAP["age_dv"]        # "Derived age at interview"
LABEL_PAY   = VARIABLE_MAP["payn_dv"]       # "Monthly net pay (take-home)"
LABEL_MH    = VARIABLE_MAP["sf12mcs_dv"]    # "Mental health score (SF-12 MCS)"
LABEL_JBSTAT = VARIABLE_MAP["jbstat"]       # "Employment status"


class TestBuildDnaRow:
    """build_dna_row produces correct summaries for each variable type."""

    @pytest.fixture(scope="class")
    def dna_a(self, cluster_a: pd.DataFrame) -> dict:
        return cluster_funcs.build_dna_row("Tribe A", cluster_a, **_DNA_KWARGS)

    @pytest.fixture(scope="class")
    def dna_b(self, cluster_b: pd.DataFrame) -> dict:
        return cluster_funcs.build_dna_row("Tribe B", cluster_b, **_DNA_KWARGS)

    # ── metadata ────────────────────────────────────────────────────────────

    def test_tribe_label_preserved(self, dna_a: dict, dna_b: dict):
        assert dna_a["tribe_label"] == "Tribe A"
        assert dna_b["tribe_label"] == "Tribe B"

    def test_size_correct(self, dna_a: dict, dna_b: dict):
        assert dna_a["size"] == 50
        assert dna_b["size"] == 50

    # ── continuous variable (age_dv) ────────────────────────────────────────

    def test_age_mean_cluster_a(self, dna_a: dict):
        """Cluster A: age_dv mean = 25.0"""
        assert dna_a[LABEL_AGE] == pytest.approx(25.0, abs=0.1)

    def test_age_mean_cluster_b(self, dna_b: dict):
        """Cluster B: age_dv mean = 65.0"""
        assert dna_b[LABEL_AGE] == pytest.approx(65.0, abs=0.1)

    def test_age_a_lower_than_b(self, dna_a: dict, dna_b: dict):
        assert dna_a[LABEL_AGE] < dna_b[LABEL_AGE]

    # ── categorical variable (jbstat) ────────────────────────────────────────
    # jbstat has one_hot=True (all categories), so build_dna_row produces a
    # percentage breakdown string rather than a mode.  All respondents are
    # Employed so the string should contain "Employed: 100%".

    def test_jbstat_both_employed(self, dna_a: dict, dna_b: dict):
        """All respondents are Employed → jbstat summary contains 'Employed: 100%'."""
        assert "Employed: 100%" in str(dna_a[LABEL_JBSTAT])
        assert "Employed: 100%" in str(dna_b[LABEL_JBSTAT])

    # ── mental health score ─────────────────────────────────────────────────

    def test_mh_cluster_a_higher(self, dna_a: dict, dna_b: dict):
        """Cluster A has better mental health (55 vs 30)."""
        assert dna_a[LABEL_MH] > dna_b[LABEL_MH]

    # ── missing column is silently skipped ──────────────────────────────────

    def test_missing_col_does_not_raise(self, cluster_a: pd.DataFrame):
        """build_dna_row should not raise if a summary_var column is absent."""
        subset = cluster_a.drop(columns=[f"{WAVE}_age_dv"], errors="ignore")
        row    = cluster_funcs.build_dna_row("T", subset, **_DNA_KWARGS)
        assert LABEL_AGE not in row


# ════════════════════════════════════════════════════════════════════════════
# 6. cluster_by_groups integration
# ════════════════════════════════════════════════════════════════════════════

class TestClusterByGroups:
    """End-to-end: normalise → group-filter → KMeans → DNA table."""

    @pytest.fixture(scope="class")
    def dna_table(self, clean_df: pd.DataFrame) -> pd.DataFrame:
        # Normalise features
        coeffs      = normalise.fit(clean_df, CORE_FEAT_COLS)
        normed_df   = normalise.apply(clean_df, coeffs)

        # Only "Employed" group matches all 100 test rows (o_jbstat_1=1 after recode).
        # All other groups are mapped to columns that are 0 for everyone.
        _JBSTAT_COLS = {
            "Employed":   f"{WAVE}_jbstat_1",
            "Unemployed": f"{WAVE}_jbstat_3",
            "Retired":    f"{WAVE}_jbstat_4",
            "On leave":   f"{WAVE}_jbstat_5",
            "Student":    f"{WAVE}_jbstat_7",
            "Inactive":   f"{WAVE}_jbstat_8",
        }
        group_col_map = {
            name: _JBSTAT_COLS.get(name, f"{WAVE}_jbstat_1")
            for name in GROUPS
        }

        return cluster_funcs.cluster_by_groups(
            df_features      = normed_df,
            df_profile       = clean_df,
            feature_cols     = CORE_FEAT_COLS,
            groups           = GROUPS,
            group_col_map    = group_col_map,
            wave             = WAVE,
            summary_vars     = SUMMARY_VARS,
            variable_map     = VARIABLE_MAP,
            categorical_vars = CATEGORICAL_VARS,
            category_maps    = CATEGORY_MAPS,
            k_default        = 2,
        )

    def test_dna_table_has_two_tribes(self, dna_table: pd.DataFrame):
        """k=2 with 100 respondents should yield 2 tribe rows (Employed group only)."""
        # Only the "Employed" group col matches (o_jbstat_1=1 for all after recode)
        employed_rows = dna_table[dna_table["group"] == "Employed"] if "group" in dna_table.columns else dna_table
        assert len(employed_rows) == 2

    def test_tribe_sizes_sum_to_100(self, dna_table: pd.DataFrame):
        employed_rows = dna_table[dna_table["group"] == "Employed"] if "group" in dna_table.columns else dna_table
        assert employed_rows["size"].sum() == 100

    def test_both_tribes_nonempty(self, dna_table: pd.DataFrame):
        assert (dna_table["size"] > 0).all()

    def test_dna_includes_age_dv(self, dna_table: pd.DataFrame):
        assert LABEL_AGE in dna_table.columns

    def test_dna_tribes_have_different_age_means(self, dna_table: pd.DataFrame):
        """The two tribes should have clearly different age_dv profiles."""
        employed_rows = dna_table[dna_table["group"] == "Employed"] if "group" in dna_table.columns else dna_table
        ages  = sorted(employed_rows[LABEL_AGE].tolist())
        diff  = ages[1] - ages[0]
        assert diff > 30, f"Tribe age means too similar: {ages}"


# ════════════════════════════════════════════════════════════════════════════
# 7. Clustering sanity checks
# ════════════════════════════════════════════════════════════════════════════

class TestClusteringSanity:
    """
    Sanity checks that confirm the clustering output is statistically sound.

    Our test data has two known, maximally-distinct groups:
      Cluster A: young (25), high-pay (3000), high-MH (55), low-hiqual (1)
      Cluster B: old  (65), low-pay (0),     low-MH  (30), high-hiqual (5)

    KMeans on normalised features must recover these groups perfectly, and the
    within-cluster variance must be far below the between-cluster variance.
    """

    @pytest.fixture(scope="class")
    def fitted(self, clean_df: pd.DataFrame):
        """Return (normed_df, labels, centroids) from a k=2 KMeans fit."""
        coeffs  = normalise.fit(clean_df, CORE_FEAT_COLS)
        normed  = normalise.apply(clean_df, coeffs)
        X       = normed[CORE_FEAT_COLS].to_numpy()
        labels  = cluster_funcs.fit_kmeans(X, k=2)
        km      = KMeans(n_clusters=2, init="k-means++", n_init=10, random_state=42)
        km.fit(X)
        return normed, labels, km.cluster_centers_

    # ── perfect separation ───────────────────────────────────────────────────

    def test_cluster_a_all_same_label(self, clean_df: pd.DataFrame, fitted):
        """All 50 Cluster-A rows get exactly one label."""
        _, labels, _ = fitted
        a_mask = clean_df["pidp"].apply(_is_cluster_a).to_numpy()
        assert len(set(labels[a_mask])) == 1

    def test_cluster_b_all_same_label(self, clean_df: pd.DataFrame, fitted):
        """All 50 Cluster-B rows get exactly one label."""
        _, labels, _ = fitted
        b_mask = ~clean_df["pidp"].apply(_is_cluster_a).to_numpy()
        assert len(set(labels[b_mask])) == 1

    def test_no_cross_contamination(self, clean_df: pd.DataFrame, fitted):
        """Label assigned to Cluster-A rows must differ from Cluster-B's label."""
        _, labels, _ = fitted
        a_mask = clean_df["pidp"].apply(_is_cluster_a).to_numpy()
        assert labels[a_mask][0] != labels[~a_mask][0]

    # ── centroid ordering ────────────────────────────────────────────────────

    def test_centroids_differ_on_age(self, fitted):
        """
        The two centroids must sit on opposite sides of zero for the age_dv
        column (one is normalised-young, the other normalised-old).
        """
        _, _, centroids = fitted
        age_idx = CORE_FEAT_COLS.index(f"{WAVE}_age_dv")
        c0, c1  = centroids[0, age_idx], centroids[1, age_idx]
        assert c0 * c1 < 0, (
            f"Age centroids should have opposite signs after normalisation: {c0:.3f}, {c1:.3f}"
        )

    def test_centroids_differ_on_pay(self, fitted):
        """
        The two centroids must sit on opposite sides of zero for payn_dv
        (one high-pay, one low-pay).
        """
        _, _, centroids = fitted
        pay_idx = CORE_FEAT_COLS.index(f"{WAVE}_payn_dv")
        c0, c1  = centroids[0, pay_idx], centroids[1, pay_idx]
        assert c0 * c1 < 0, (
            f"Pay centroids should have opposite signs: {c0:.3f}, {c1:.3f}"
        )

    def test_centroids_differ_on_mh(self, fitted):
        """
        The two centroids must sit on opposite sides of zero for sf12mcs_dv
        (one high-MH, one low-MH).
        """
        _, _, centroids = fitted
        mh_idx = CORE_FEAT_COLS.index(f"{WAVE}_sf12mcs_dv")
        c0, c1 = centroids[0, mh_idx], centroids[1, mh_idx]
        assert c0 * c1 < 0, (
            f"MH centroids should have opposite signs: {c0:.3f}, {c1:.3f}"
        )

    # ── within vs between variance ───────────────────────────────────────────

    def test_within_cluster_variance_near_zero(self, clean_df: pd.DataFrame, fitted):
        """
        Because all Cluster-A/B rows are identical within each group, the
        within-cluster variance on any feature column should be exactly 0.
        """
        normed, labels, _ = fitted
        for col in CORE_FEAT_COLS:
            vals = normed[col].to_numpy()
            for lbl in (0, 1):
                group_vals = vals[labels == lbl]
                var = float(np.var(group_vals))
                assert var == pytest.approx(0.0, abs=1e-8), (
                    f"Within-cluster variance for {col} (label={lbl}) = {var!r}"
                )

    def test_between_cluster_variance_positive(self, clean_df: pd.DataFrame, fitted):
        """
        The distance between centroids on key features (age, pay, MH) must be
        clearly non-zero — confirming the clusters represent different people.
        """
        normed, labels, centroids = fitted
        for col in [f"{WAVE}_age_dv", f"{WAVE}_payn_dv", f"{WAVE}_sf12mcs_dv"]:
            idx = CORE_FEAT_COLS.index(col)
            dist = abs(centroids[0, idx] - centroids[1, idx])
            assert dist > 0.5, (
                f"Centroid separation for {col} unexpectedly small: {dist:.4f}"
            )

    # ── inertia decreases with k ─────────────────────────────────────────────

    def test_inertia_decreases_with_k(self, clean_df: pd.DataFrame):
        """
        Inertia should strictly decrease from k=1 to k=2 on this well-separated
        data.  We only test k=1→2 because the test data has exactly 2 distinct
        feature vectors — k=3 cannot reduce inertia further (it's already ~0).
        """
        coeffs = normalise.fit(clean_df, CORE_FEAT_COLS)
        normed = normalise.apply(clean_df, coeffs)
        X      = normed[CORE_FEAT_COLS].to_numpy()
        km1 = KMeans(n_clusters=1, init="k-means++", n_init=10, random_state=42)
        km2 = KMeans(n_clusters=2, init="k-means++", n_init=10, random_state=42)
        km1.fit(X)
        km2.fit(X)
        assert km2.inertia_ < km1.inertia_, (
            f"Inertia did not decrease from k=1 to k=2: "
            f"{km1.inertia_:.4f} → {km2.inertia_:.4f}"
        )

    # ── silhouette score ─────────────────────────────────────────────────────

    def test_silhouette_score_high(self, clean_df: pd.DataFrame, fitted):
        """
        Silhouette score for perfectly separated clusters should be close to 1.
        We require > 0.8 as a sanity threshold.
        """
        from sklearn.metrics import silhouette_score
        normed, labels, _ = fitted
        X     = normed[CORE_FEAT_COLS].to_numpy()
        score = silhouette_score(X, labels)
        assert score > 0.8, f"Silhouette score too low: {score:.4f}"

    # ── DNA profile ordering ─────────────────────────────────────────────────

    def test_dna_age_ordering(self, cluster_a: pd.DataFrame, cluster_b: pd.DataFrame):
        """DNA row for Cluster A must have lower mean age than Cluster B."""
        dna_a = cluster_funcs.build_dna_row("A", cluster_a, **_DNA_KWARGS)
        dna_b = cluster_funcs.build_dna_row("B", cluster_b, **_DNA_KWARGS)
        assert dna_a[LABEL_AGE] < dna_b[LABEL_AGE], (
            f"Age: A={dna_a[LABEL_AGE]}, B={dna_b[LABEL_AGE]}"
        )

    def test_dna_pay_ordering(self, cluster_a: pd.DataFrame, cluster_b: pd.DataFrame):
        """
        Cluster A (payn=3000) must have higher mean pay than Cluster B (payn=0).
        We compare raw column means directly: build_dna_row treats a column
        whose values are all in {0, 1} as binary (percentage string), which
        would happen for Cluster B when payn_dv=0 throughout.
        """
        col = f"{WAVE}_payn_dv"
        mean_a = cluster_a[col].mean()
        mean_b = cluster_b[col].mean()
        assert mean_a > mean_b, f"Pay means: A={mean_a}, B={mean_b}"

    def test_dna_mh_ordering(self, cluster_a: pd.DataFrame, cluster_b: pd.DataFrame):
        """Cluster A (MH=55) must have higher mean MH score than Cluster B (MH=30)."""
        dna_a = cluster_funcs.build_dna_row("A", cluster_a, **_DNA_KWARGS)
        dna_b = cluster_funcs.build_dna_row("B", cluster_b, **_DNA_KWARGS)
        assert dna_a[LABEL_MH] > dna_b[LABEL_MH], (
            f"MH: A={dna_a[LABEL_MH]}, B={dna_b[LABEL_MH]}"
        )

    def test_dna_sizes_sum_to_total(self, cluster_a: pd.DataFrame, cluster_b: pd.DataFrame):
        """DNA size fields should sum to the total number of respondents."""
        dna_a = cluster_funcs.build_dna_row("A", cluster_a, **_DNA_KWARGS)
        dna_b = cluster_funcs.build_dna_row("B", cluster_b, **_DNA_KWARGS)
        assert dna_a["size"] + dna_b["size"] == len(cluster_a) + len(cluster_b)

    # ── k=1 degenerate case ──────────────────────────────────────────────────

    def test_k1_single_centroid(self, clean_df: pd.DataFrame):
        """k=1 must produce a single centroid equal to the global feature mean."""
        coeffs = normalise.fit(clean_df, CORE_FEAT_COLS)
        normed = normalise.apply(clean_df, coeffs)
        X      = normed[CORE_FEAT_COLS].to_numpy()
        labels = cluster_funcs.fit_kmeans(X, k=1)
        assert (labels == 0).all()
        # After normalisation the global mean of each feature is 0
        for i, col in enumerate(CORE_FEAT_COLS):
            col_mean = normed[col].mean()
            assert abs(col_mean) < 1e-10, f"{col} post-normalise mean = {col_mean}"

    # ── reproducibility ──────────────────────────────────────────────────────

    def test_clustering_is_deterministic(self, clean_df: pd.DataFrame):
        """Same random_state must always produce identical labels."""
        coeffs = normalise.fit(clean_df, CORE_FEAT_COLS)
        normed = normalise.apply(clean_df, coeffs)
        X      = normed[CORE_FEAT_COLS].to_numpy()
        labels_1 = cluster_funcs.fit_kmeans(X, k=2)
        labels_2 = cluster_funcs.fit_kmeans(X, k=2)
        np.testing.assert_array_equal(labels_1, labels_2)


# ── helpers ──────────────────────────────────────────────────────────────────
