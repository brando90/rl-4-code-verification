"""Unit tests for experiment 10's promotion-policy replay, including the reviewers' deterministic counterexamples."""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/expt_v1/analyze_e10.py"


@pytest.fixture(scope="module")
def e10():
    spec = importlib.util.spec_from_file_location("analyze_e10", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["analyze_e10"] = module  # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(module)
    return module


def _matrix(e10, r, g, tf, tk):
    r, g, tf, tk = (np.asarray(x, float) for x in (r, g, tf, tk))
    return e10.Matrix([f"s{i}" for i in range(r.shape[0])], [f"t{j}" for j in range(r.shape[1])], r, g, g * tf, g * tk)


def _write_cells(path, rows):
    path.write_bytes(gzip.compress("\n".join(json.dumps(r) for r in rows).encode()))


def test_pair_statistics_by_hand(e10):
    # s0 resolves t0, t1; s1 fixes t2, t3 but breaks t0 (FAIL_TO_PASS) and t1 (PASS_TO_PASS 1 -> 0.5).
    r = [[1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 0, 0]]
    g = [[1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 0, 1]]
    tf = [[1, 1, 0, 0.5], [0, 1, 1, 1], [0, 0, 0, 0.5]]
    tk = [[1, 1, 1, 1], [1, 0.5, 1, 1], [1, 1, 0, 0.5]]
    m = _matrix(e10, r, g, tf, tk)
    pt = e10.pair_tensors(m)
    gains, losses = (1 - m.r) @ m.r.T, m.r @ (1 - m.r).T
    assert gains[0, 1] == 2 and losses[0, 1] == 2
    assert float(pt.drop_total[0, 1].sum()) == pytest.approx(1.5)  # t0 tf 1->0; t1 tk 1->0.5
    assert float(pt.drop_hidden[0, 2].sum()) == pytest.approx(2.5)  # t2 gate lost (1,0,1)->0; t3 tk 1->0.5
    assert float(pt.drop_keep_hidden[0, 2].sum()) == pytest.approx(1.5)
    assert float(pt.drop_gate_loss[0, 2].sum()) == pytest.approx(2.0)
    assert float(pt.drop_gate_loss[1, 2].sum()) == pytest.approx(3.0)  # a flip (s1 resolved t2), so not hidden
    assert float(pt.drop_hidden[1, 2].sum()) == pytest.approx(1.0)  # only t1 (jointly unresolved): tf 1 -> 0


def test_split_pairs_counts_on_validation_half(e10):
    rng = np.random.default_rng(0)
    r = (rng.random((5, 20)) < 0.5).astype(float)
    g = np.ones_like(r)
    m = _matrix(e10, r, g, np.where(r == 1, 1.0, rng.random(r.shape)), np.where(r == 1, 1.0, rng.random(r.shape)))
    pt = e10.pair_tensors(m)
    val = np.zeros(20, bool)
    val[:10] = True
    st = e10.split_pairs(m, pt, val, near_max_gain=2)
    rv, rt = r[:, :10], r[:, 10:]
    assert np.array_equal(st["gains_v"], (1 - rv) @ rv.T) and np.array_equal(st["losses_v"], rv @ (1 - rv).T)
    assert np.allclose(st["trm_v"], pt.drop_total[:, :, :10].sum(-1) / 10)
    assert np.allclose(st["dpass_t"], ((1 - rt) @ rt.T - rt @ (1 - rt).T) / 10)
    assert not st["eligible"][np.arange(5), np.arange(5)].any()
    assert (st["net_v"][st["near"]] <= 2).all() and (st["net_v"][st["near"]] > 0).all()


def test_selected_weights_identity_keeps_floor_qn_whole_pairs(e10):
    kept = e10.selected_weights(np.array([3, 0, 4, 1, 2]), np.ones((1, 5)), 0.5)
    assert kept[0].tolist() == [1.0, 0.0, 0.0, 1.0, 0.0]  # first floor(2.5) = 2 of the order: 3, 0


def test_selected_weights_match_across_orders_under_bootstrap_weights(e10):
    # Reviewer counterexample: weights [2, 1, 0], q = 0.5; an indivisible prefix kept 0 for one order and 1 for another.
    w = np.array([[2.0, 1.0, 0.0]])
    for order in ([0, 1, 2], [1, 0, 2], [2, 1, 0], [2, 0, 1]):
        kept = e10.selected_weights(np.array(order), w, 0.5)
        assert kept.sum() == pytest.approx(1.0)  # floor(0.5 * 3) for every policy order
        assert (kept <= w + 1e-12).all() and (kept >= 0).all()


def test_weighted_ranks_ones_duplication_and_empty(e10):
    x = np.array([3.0, 1.0, 2.0, 2.0, 5.0])
    assert e10.weighted_ranks(x, np.ones((1, 5)))[0].tolist() == [3.5, 0.5, 2.0, 2.0, 4.5]
    w = np.array([[2.0, 1.0, 1.0, 1.0, 1.0]])
    rd = e10.weighted_ranks(np.r_[x, x[0]], np.ones((1, 6)))[0]
    assert e10.weighted_ranks(x, w)[0][0] == pytest.approx(rd[0])
    assert e10.weighted_ranks(np.array([]), np.ones((3, 0))).shape == (3, 0)


def test_weighted_partial_corr_equals_duplicated_data(e10):
    rng = np.random.default_rng(1)
    n = 60
    c1, c2 = rng.random(n), rng.random(n)
    y = c1 + rng.normal(0, 0.3, n)
    z = 0.5 * y + c2 + rng.normal(0, 0.3, n)
    counts = rng.integers(0, 3, n).astype(float)
    weighted = e10.weighted_partial_corr(y, z, [c1, c2], counts[None, :])[0]
    rep = np.repeat(np.arange(n), counts.astype(int))
    dup = e10.weighted_partial_corr(y[rep], z[rep], [c1[rep], c2[rep]], np.ones((1, len(rep))))[0]
    assert weighted == pytest.approx(dup, abs=1e-9) and -1 <= weighted <= 1


def test_partial_corr_defined_for_nearly_collinear_but_well_posed_design(e10):
    # Reviewer counterexample: covariate ranks differing by one adjacent swap; the design is fine (cond ~ 2e5)
    # although the normal matrix's condition is ~4e10. The correlation must be defined.
    rng = np.random.default_rng(2)
    n = 3000
    c1 = np.arange(n, dtype=float)
    c2 = c1.copy()
    c2[[10, 11]] = c2[[11, 10]]
    y = c1 / n + rng.normal(0, 0.3, n)
    z = 0.6 * y + rng.normal(0, 0.3, n)
    val = e10.weighted_partial_corr(y, z, [c1, c2], np.ones((1, n)))[0]
    assert np.isfinite(val) and 0 < val < 1


def test_partial_corr_undefined_for_exactly_collinear_design(e10):
    rng = np.random.default_rng(3)
    c = rng.random(100)
    val = e10.weighted_partial_corr(rng.random(100), rng.random(100), [c, c], np.ones((1, 100)))[0]
    assert np.isnan(val)


def test_aggregate_family_uses_common_support_and_invalidates_draws(e10):
    # Reviewer counterexample: splits [[.2, .8], [.4, NaN]] (columns: point, draw). Point = .3 on both splits;
    # the draw is invalid (undefined on an admitted split), not silently averaged over one split.
    out = e10.aggregate_family({"x": [np.array([0.2, 0.8]), np.array([0.4, np.nan])]}, 2)
    assert out["members"]["x"]["estimate"] == pytest.approx(0.3)
    assert out["draws_valid"] == 0 and out["draws_total"] == 1
    assert out["status"].startswith("inconclusive")
    # A member undefined at the point estimate removes that split for the whole family.
    out = e10.aggregate_family({"a": [np.array([0.1]), np.array([0.3])], "b": [np.array([1.0]), np.array([np.nan])]}, 2)
    assert out["splits_admitted"] == 1 and out["members"]["a"]["estimate"] == pytest.approx(0.1)


def test_zero_denominators_are_undefined_not_zero(e10):
    out = e10._ratio(np.array([0.0, 1.0]), np.array([0.0, 2.0]))
    assert np.isnan(out[0]) and out[1] == 0.5


def test_unstratified_risk_policies_have_no_gain_preference(e10):
    # Reviewer counterexample: equal penalties, gains [1, 2], ascending hashes [0, 1] -> order follows the hash.
    st = {"net_v": np.array([[1, 2]]), "dscs_v": np.zeros((1, 2)), "losses_v": np.zeros((1, 2)),
          "trm_v": np.zeros((1, 2)), "hrm_v": np.zeros((1, 2))}
    orders = e10.policy_orders(st, np.array([0, 1]), np.array([[0.0, 1.0]]))
    assert orders["S2"].tolist() == [0, 1] and orders["S3"].tolist() == [0, 1]
    assert orders["S0plus"].tolist() == [1, 0]  # the stricter scalar rule still prefers the larger gain


def test_bootstrap_weights_are_products_of_multiplicities(e10):
    w = e10.bootstrap_weights(6, 3, seed=7)
    assert w.shape == (4, 6, 6) and np.all(w[0] == 1)
    m = np.random.default_rng(7).multinomial(6, np.full(6, 1 / 6), size=3)
    assert np.array_equal(w[1:], m[:, :, None] * m[:, None, :])


def test_binary_policy_ranks_zero_loss_candidate_first(e10):
    r = np.array([[1, 1, 0, 0, 0, 0], [0, 0, 1, 1, 1, 0], [1, 1, 1, 0, 0, 0]], float)
    m = _matrix(e10, r, np.ones_like(r), r, np.ones_like(r))
    st = e10.split_pairs(m, e10.pair_tensors(m), np.array([True] * 5 + [False]), near_max_gain=5)
    idx = np.flatnonzero(st["near"].ravel())
    pairs = [(int(st["inc"].ravel()[i]), int(st["cand"].ravel()[i])) for i in idx]
    orders = e10.policy_orders(st, idx, e10.pair_hash(m.systems))
    assert pairs[orders["S2"][0]] == (0, 2)  # fix-3-break-2 (0 -> 1) is ranked after the zero-loss candidate


def test_load_matrix_validation(tmp_path, e10):
    def rows(**over):
        base = []
        for s in ("a", "b"):
            for t in ("x", "y"):
                gate = 0 if (s, t) == ("b", "y") else 1
                base.append({"submission": s, "instance_id": t, "included": True, "common_cohort": True, "gate": gate,
                             "t_fix": None if gate == 0 else 0.5, "t_keep": None if gate == 0 else 1.0, "resolved": False})
        base[0].update(over)
        return base
    p = tmp_path / "cells.jsonl.gz"
    _write_cells(p, rows())
    with pytest.raises(SystemExit):
        e10.load_matrix(p, expect_sha="0" * 64)
    m = e10.load_matrix(p, expect_sha=None)
    assert m.gf.tolist() == [[0.5, 0.5], [0.5, 0.0]] and m.g.tolist() == [[1, 1], [1, 0]]
    for bad in ({"resolved": None}, {"gate": None}, {"gate": True}, {"t_fix": 1.5}, {"t_keep": float("nan")}):
        _write_cells(p, rows(**bad))
        with pytest.raises(SystemExit):
            e10.load_matrix(p, expect_sha=None)
    _write_cells(p, rows() + [rows()[0]])
    with pytest.raises(SystemExit):
        e10.load_matrix(p, expect_sha=None)


def test_empty_population_is_degenerate_not_a_crash(tmp_path, e10):
    # Reviewer counterexample: 4 systems x 424 all-unresolved tasks crashed in weighted_ranks before the rule ran.
    rows = [{"submission": f"s{i}", "instance_id": f"t{j:03d}", "included": True, "common_cohort": True, "gate": 1,
             "t_fix": 0.0, "t_keep": 1.0, "resolved": False} for i in range(4) for j in range(424)]
    p = tmp_path / "empty.jsonl.gz"
    _write_cells(p, rows)
    args = argparse.Namespace(per_cell=str(p), expect_sha=None, sensitivity="none", splits=3, draws=5,
                              split_seed=1, boot_seed=2, near_band=0.05, q=[0.5], min_pairs=200, workers=1, out="unused")
    res = e10.run(args)
    near = res["populations"]["near"]
    assert near["splits_degenerate"] == 3 and near["status"].startswith("inconclusive")
