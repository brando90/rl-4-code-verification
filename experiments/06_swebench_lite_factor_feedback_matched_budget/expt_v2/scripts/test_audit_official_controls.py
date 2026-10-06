"""Test fail-closed control accounting on synthetic reports, never benchmark references."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("control_summary", Path(__file__).with_name("audit_official_controls.py"))
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


def report(resolved=False):
    return {"resolved": resolved, "patch_successfully_applied": True}


def test_import_abort_is_null_even_with_a_false_grader_report():
    assert summary.classify(report(), "ImportError while loading conftest") == (
        "import_failure_before_test_completion", None)


def test_fixture_failure_is_null_even_with_a_pytest_summary():
    output = "AttributeError: 'TestSyntheticFixture' object has no attribute 'state'\n2 failed, 8 passed in 1.0s"
    assert summary.classify(report(), output) == ("fixture_failure_requires_environment_validation", None)


def test_a_valid_test_failure_remains_false():
    assert summary.classify(report(), "1 failed, 8 passed in 1.0s") == ("test_execution_observed", False)


def test_expected_import_exception_inside_completed_tests_is_not_an_abort():
    assert summary.classify(report(True), "expected ImportError was caught\n2 passed in 1.0s") == (
        "test_execution_observed", True)


@pytest.mark.parametrize("value", [None, {}, {"resolved": 0}, {"resolved": False}])
def test_absent_or_ambiguous_evidence_is_never_zero_imputed(value):
    assert summary.classify(value, "")[1] is None


def test_missing_test_completion_is_null():
    assert summary.classify(report(), "setup output only")[1] is None


def test_duplicate_completed_receipts_require_reconciliation():
    values = [{"instance_id": "synthetic", "kind": "gold", "status": "COMPLETE"}] * 2
    with pytest.raises(ValueError, match="multiple completed receipts"):
        summary.select(values, "synthetic", "gold")


def test_marker_variant_cannot_fill_an_exact_empty_cell():
    assert summary.select([{"instance_id": "synthetic", "kind": "empty", "status": "COMPLETE"}],
                          "synthetic", "exact_empty_patch_adapter") is None
