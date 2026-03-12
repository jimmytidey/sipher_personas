# tests/test_api.py
#
# API tests using FastAPI's TestClient (httpx under the hood).
#
# Run from the project root:
#
#     venv/bin/pytest tests/test_api.py -v
#
# All tests use ?test=true so they read from data_test/6_cluster/LA_clusters.csv.
# The test cluster CSV contains 2 LAs (E99000001, E99000002), each with 2
# Employed tribes of size 25 — produced by running the pipeline on test data.

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.main import app

client = TestClient(app, raise_server_exceptions=True)

# ── Known test-data constants ─────────────────────────────────────────────────
TEST_LA_CODES    = {"E99000001", "E99000002"}
TEST_LA_NAMES    = {"E99000001": "Test Borough A", "E99000002": "Test Borough B"}
TEST_GROUP       = "Employed"
TEST_TRIBES_PER_LA = 2
TEST_TOTAL_SIZE  = 50   # 25 + 25 per LA


# ════════════════════════════════════════════════════════════════════════════
# 1. Health
# ════════════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


# ════════════════════════════════════════════════════════════════════════════
# 2. /las — list local authorities
# ════════════════════════════════════════════════════════════════════════════

class TestListLAs:

    @pytest.fixture(scope="class")
    def las(self) -> list[dict]:
        r = client.get("/las?test=true")
        assert r.status_code == 200
        return r.json()

    def test_status_200(self):
        assert client.get("/las?test=true").status_code == 200

    def test_returns_list(self, las):
        assert isinstance(las, list)

    def test_two_las_returned(self, las):
        assert len(las) == 2

    def test_la_codes_correct(self, las):
        codes = {item["code"] for item in las}
        assert codes == TEST_LA_CODES

    def test_la_names_populated(self, las):
        """Names should come from the geography CSV, not fall back to the code."""
        name_map = {item["code"]: item["name"] for item in las}
        assert name_map["E99000001"] == "Test Borough A"
        assert name_map["E99000002"] == "Test Borough B"

    def test_sorted_by_code(self, las):
        codes = [item["code"] for item in las]
        assert codes == sorted(codes)

    def test_each_item_has_code_and_name(self, las):
        for item in las:
            assert "code" in item
            assert "name" in item


# ════════════════════════════════════════════════════════════════════════════
# 3. /la/{ladcd}/groups
# ════════════════════════════════════════════════════════════════════════════

class TestGetGroups:

    def test_known_la_returns_200(self):
        assert client.get("/la/E99000001/groups?test=true").status_code == 200

    def test_unknown_la_returns_404(self):
        assert client.get("/la/E00UNKNOWN/groups?test=true").status_code == 404

    def test_returns_employed_group(self):
        r = client.get("/la/E99000001/groups?test=true")
        groups = r.json()
        assert isinstance(groups, list)
        assert TEST_GROUP in groups

    def test_both_las_have_same_groups(self):
        g1 = client.get("/la/E99000001/groups?test=true").json()
        g2 = client.get("/la/E99000002/groups?test=true").json()
        assert sorted(g1) == sorted(g2)

    def test_groups_sorted(self):
        groups = client.get("/la/E99000001/groups?test=true").json()
        assert groups == sorted(groups)


# ════════════════════════════════════════════════════════════════════════════
# 4. /la/{ladcd}/personas
# ════════════════════════════════════════════════════════════════════════════

class TestGetPersonas:

    @pytest.fixture(scope="class")
    def personas_la1(self) -> list[dict]:
        r = client.get("/la/E99000001/personas?test=true")
        assert r.status_code == 200
        return r.json()

    @pytest.fixture(scope="class")
    def personas_la2(self) -> list[dict]:
        r = client.get("/la/E99000002/personas?test=true")
        assert r.status_code == 200
        return r.json()

    # ── status codes ─────────────────────────────────────────────────────────

    def test_known_la_returns_200(self):
        assert client.get("/la/E99000001/personas?test=true").status_code == 200

    def test_unknown_la_returns_404(self):
        assert client.get("/la/E00UNKNOWN/personas?test=true").status_code == 404

    def test_unknown_group_returns_404(self):
        r = client.get("/la/E99000001/personas?test=true&group=Nonexistent")
        assert r.status_code == 404

    # ── shape ────────────────────────────────────────────────────────────────

    def test_returns_two_tribes_per_la(self, personas_la1, personas_la2):
        assert len(personas_la1) == TEST_TRIBES_PER_LA
        assert len(personas_la2) == TEST_TRIBES_PER_LA

    def test_required_fields_present(self, personas_la1):
        for persona in personas_la1:
            assert "tribe_label" in persona
            assert "size"        in persona
            assert "unit_id"     in persona
            assert "group"       in persona
            assert "cluster_level" in persona

    # ── unit_id / group / cluster_level values ───────────────────────────────

    def test_unit_id_matches_la_code(self, personas_la1, personas_la2):
        assert all(p["unit_id"] == "E99000001" for p in personas_la1)
        assert all(p["unit_id"] == "E99000002" for p in personas_la2)

    def test_group_is_employed(self, personas_la1):
        """All test tribes belong to the Employed group."""
        assert all(p["group"] == TEST_GROUP for p in personas_la1)

    def test_cluster_level_is_la(self, personas_la1):
        assert all(p["cluster_level"] == "LA" for p in personas_la1)

    # ── sizes ────────────────────────────────────────────────────────────────

    def test_tribe_sizes_are_positive(self, personas_la1):
        assert all(p["size"] > 0 for p in personas_la1)

    def test_total_size_per_la(self, personas_la1, personas_la2):
        """Both tribes together should cover all 50 test respondents per LA."""
        assert sum(p["size"] for p in personas_la1) == TEST_TOTAL_SIZE
        assert sum(p["size"] for p in personas_la2) == TEST_TOTAL_SIZE

    def test_tribes_have_distinct_labels(self, personas_la1):
        labels = [p["tribe_label"] for p in personas_la1]
        assert len(set(labels)) == len(labels)

    # ── group filter ─────────────────────────────────────────────────────────

    def test_group_filter_returns_subset(self):
        all_r    = client.get("/la/E99000001/personas?test=true").json()
        filt_r   = client.get(f"/la/E99000001/personas?test=true&group={TEST_GROUP}").json()
        assert len(filt_r) <= len(all_r)
        assert all(p["group"] == TEST_GROUP for p in filt_r)

    def test_group_filter_matches_unfiltered_for_employed(self):
        """Since all test tribes are Employed, filtering by Employed = all rows."""
        all_r  = client.get("/la/E99000001/personas?test=true").json()
        filt_r = client.get(f"/la/E99000001/personas?test=true&group={TEST_GROUP}").json()
        assert len(filt_r) == len(all_r)

    # ── profile data sanity ──────────────────────────────────────────────────

    def test_both_las_return_same_profile_shape(self, personas_la1, personas_la2):
        """Same columns should be present for both LAs."""
        cols1 = sorted(personas_la1[0].keys())
        cols2 = sorted(personas_la2[0].keys())
        assert cols1 == cols2

    def test_no_extra_unit_ids_in_la1_response(self, personas_la1):
        """Filtering by LA should not leak rows from other LAs."""
        unit_ids = {p["unit_id"] for p in personas_la1}
        assert unit_ids == {"E99000001"}


# ════════════════════════════════════════════════════════════════════════════
# 5. Prod vs test mode separation
# ════════════════════════════════════════════════════════════════════════════

class TestTestFlag:
    """?test=true and default (prod) mode must read different datasets."""

    def test_test_mode_returns_test_la_codes(self):
        codes = {la["code"] for la in client.get("/las?test=true").json()}
        assert codes == TEST_LA_CODES

    def test_test_la_codes_absent_from_prod_if_prod_exists(self):
        """Test LA codes (E99*) should never appear in production data."""
        import os
        from api.main import PROD_CLUSTERS_PATH
        if not PROD_CLUSTERS_PATH.exists():
            pytest.skip("Production cluster file not found — skipping prod check")
        prod_las = {la["code"] for la in client.get("/las").json()}
        assert not (prod_las & TEST_LA_CODES), \
            f"Test LA codes found in prod data: {prod_las & TEST_LA_CODES}"

    def test_persona_404_in_test_mode_for_real_la(self):
        """A real London LA code should 404 in test mode (not in test dataset)."""
        r = client.get("/la/E09000001/personas?test=true")
        assert r.status_code == 404
