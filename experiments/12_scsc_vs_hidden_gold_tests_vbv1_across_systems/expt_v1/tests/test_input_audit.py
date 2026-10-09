"""Protect the preflight against conflating aggregations, imputing missing factors, or misbinding files."""

import hashlib
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("audit_inputs_e12", Path(__file__).parents[1] / "scripts/audit_inputs_e12.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_distinguishes_geometric_of_means_from_mean_of_geometric():
    rows = [{"IC_tests": 1., "IC_proofs": 1., "FSC": 1.},
            {"IC_tests": 0., "IC_proofs": 0., "FSC": 1.}]
    result = audit.aggregate(rows, .5)
    assert result["geometric_mean_of_factor_means_measured"] == pytest.approx(.25 ** (1 / 3))
    assert result["mean_per_cell_scsc_measured"] == .5
    assert not result["matches_published_three_decimals"]
    assert result["mean_per_cell_matches_published_three_decimals"]


def test_missing_factors_are_never_zero_imputed():
    rows = [{"IC_tests": 1., "IC_proofs": 1., "FSC": 1.}] * 895
    rows += [{"IC_tests": 0., "IC_proofs": 0., "FSC": None}]
    result = audit.aggregate(rows, 1.)
    assert result["n_declared"] == 896
    assert result["n_common_measured"] == 895
    assert result["n_missing_factors"] == 1
    assert result["geometric_mean_of_factor_means_all896"] is None
    assert result["geometric_mean_of_factor_means_measured"] == 1.


def test_full_cohort_and_three_decimal_gate():
    rows = [{"IC_tests": .5, "IC_proofs": .5, "FSC": .5}] * 896
    result = audit.aggregate(rows, .5001)
    assert result["geometric_mean_of_factor_means_all896"] == .5
    assert result["matches_published_three_decimals"]
    assert not audit.aggregate(rows, .501)["matches_published_three_decimals"]


def test_empty_cohort_is_missing():
    result = audit.aggregate([{"IC_tests": None, "IC_proofs": None, "FSC": None}], 0.)
    assert result["geometric_mean_of_factor_means_measured"] is None
    assert not result["matches_published_three_decimals"]


def test_hash_binding_rejects_wrong_recovery_bytes(tmp_path):
    original, recovery = tmp_path / "original.lean", tmp_path / "recovery.lean"
    original.write_text("original")
    recovery.write_text("recovered")
    expected = hashlib.sha256(b"original").hexdigest()
    result = audit.resolve_candidate([recovery, original], expected)
    assert result["path"] == str(original)
    assert result["join_status"] == "bound"
    assert audit.resolve_candidate([recovery], expected)["join_status"] == "hash_mismatch"


def test_no_hash_distinguishes_ambiguity_empty_and_missing(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_text("")
    b.write_text("different")
    assert audit.resolve_candidate([a, b], None)["join_status"] == "ambiguous"
    assert audit.resolve_candidate([a], None)["bytes"] == 0
    assert audit.resolve_candidate([tmp_path / "absent"], None)["join_status"] == "file_missing"
