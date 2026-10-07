"""TLDR: Unit tests for SCS4C factors, gating, system aggregation and the numpy-only rank correlations."""

import math

import pytest

from rl4cv.scs4c import (
    Cell,
    cell_from_report,
    cell_score,
    fraction_passed,
    geometric_mean,
    kendall_tau_b,
    pearson,
    spearman,
    system_summary,
)

F2P = ["t::fix_a", "t::fix_b"]
P2P = ["t::keep_a", "t::keep_b", "t::keep_c", "t::keep_d"]


def report(applied=True, f2p_ok=(), p2p_ok=(), resolved=False):
    return {
        "patch_exists": True,
        "patch_is_None": False,
        "patch_successfully_applied": applied,
        "resolved": resolved,
        "tests_status": {
            "FAIL_TO_PASS": {"success": list(f2p_ok), "failure": [t for t in F2P if t not in f2p_ok]},
            "PASS_TO_PASS": {"success": list(p2p_ok), "failure": [t for t in P2P if t not in p2p_ok]},
        },
    }


def test_fraction_passed_uses_gold_denominator_and_vacuous_empty():
    assert fraction_passed(["t::fix_a", "unrelated"], F2P) == 0.5
    assert fraction_passed([], []) == 1.0


def test_report_lists_are_the_default_denominator():
    c = cell_from_report("i", report(f2p_ok=["t::fix_a"], p2p_ok=P2P), has_patch=True)
    assert (c.t_fix, c.t_keep) == (0.5, 1.0)


def test_resolved_patch_scores_one():
    c = cell_from_report("i", report(f2p_ok=F2P, p2p_ok=P2P, resolved=True), F2P, P2P, has_patch=True)
    assert (c.gate, c.t_fix, c.t_keep, c.resolved) == (1, 1.0, 1.0, True)
    assert cell_score(c) == 1.0


def test_partial_credit_is_geometric_mean_of_test_factors():
    c = cell_from_report("i", report(f2p_ok=["t::fix_a"], p2p_ok=P2P), F2P, P2P, has_patch=True)
    assert cell_score(c) == pytest.approx(math.sqrt(0.5 * 1.0))


def test_any_zero_factor_collapses_the_score():
    c = cell_from_report("i", report(f2p_ok=[], p2p_ok=P2P), F2P, P2P, has_patch=True)
    assert cell_score(c) == 0.0


def test_gate_failure_scores_zero_and_leaves_factors_not_run():
    c = cell_from_report("i", report(applied=False), F2P, P2P, has_patch=True)
    assert c.gate == 0 and c.t_fix is None and c.t_keep is None
    assert cell_score(c) == 0.0 and c.gated("t_fix") == 0.0


def test_missing_patch_is_zero_but_missing_report_is_unmeasured():
    assert cell_score(cell_from_report("i", None, F2P, P2P, has_patch=False)) == 0.0
    unmeasured = cell_from_report("i", None, F2P, P2P, has_patch=True)
    assert unmeasured.gate is None and cell_score(unmeasured) is None


def test_system_summary_is_geometric_mean_of_factor_means_on_measured_cohort():
    cells = [
        Cell("a", 1, 1.0, 1.0, True),
        Cell("b", 1, 0.5, 1.0, False),
        Cell("c", 0, None, None, False),
        Cell("d", None, None, None, None),
    ]
    s = system_summary(cells)
    assert (s["declared"], s["measured"], s["unmeasured"]) == (4, 3, 1)
    assert s["factor_means"]["t_fix"] == pytest.approx(0.5)
    assert s["factor_means"]["t_keep"] == pytest.approx(2 / 3)
    assert s["scs4c"] == pytest.approx(math.sqrt(0.5 * 2 / 3))
    assert s["pass1"] == pytest.approx(1 / 3)
    assert s["pass1_declared"] == pytest.approx(1 / 4)


def test_geometric_mean_does_not_clamp_zero():
    assert geometric_mean([0.0, 1.0]) == 0.0
    assert geometric_mean([0.25, 1.0]) == pytest.approx(0.5)


def test_correlations_match_scipy_with_ties():
    stats = pytest.importorskip("scipy.stats")
    x = [0.1, 0.4, 0.4, 0.9, 0.3, 0.7, 0.7, 0.2]
    y = [0.2, 0.5, 0.1, 0.8, 0.3, 0.9, 0.6, 0.2]
    assert pearson(x, y) == pytest.approx(stats.pearsonr(x, y)[0])
    assert spearman(x, y) == pytest.approx(stats.spearmanr(x, y)[0])
    assert kendall_tau_b(x, y) == pytest.approx(stats.kendalltau(x, y, variant="b")[0])


def test_constant_input_has_no_correlation():
    assert pearson([1, 1, 1], [1, 2, 3]) is None
