"""Unit tests for experiment 10's promotion-gate replay (pair statistics, selection, weighted ranks, dyadic bootstrap)."""

from __future__ import annotations

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
    return e10.Matrix([f"s{i}" for i in range(r.shape[0])], [f"t{j}" for j in range(r.shape[1])],
                      r, g, g * tf, g * tk)


def test_pair_statistics_by_hand(e10):
    # s0 resolves t0, t1; s1 fixes t2, t3 but breaks t0 (FAIL_TO_PASS) and t1 (PASS_TO_PASS 1 -> 0.5).
    r = [[1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 0, 0]]
    g = [[1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 0, 1]]
    tf = [[1, 1, 0, 0.5], [0, 1, 1, 1], [0, 0, 0, 0.5]]
    tk = [[1, 1, 1, 1], [1, 0.5, 1, 1], [1, 1, 0, 0.5]]
    m = _matrix(e10, r, g, tf, tk)
    pt = e10.pair_tensors(m)
    gains = (1 - m.r) @ m.r.T
    losses = m.r @ (1 - m.r).T
    assert gains[0, 1] == 2 and losses[0, 1] == 2  # s0 -> s1: fixes t2, t3; breaks t0, t1
    # Total drop s0 -> s1 over (g, g*tf, g*tk): t0 tf 1->0 = 1; t1 tk 1->0.5 = 0.5; t2, t3 none.
    assert float(pt.drop_total[0, 1].sum()) == pytest.approx(1.5)
    # Hidden (jointly unresolved) s0 -> s2: t2 gate lost (1,0,1)->(0,0,0) = 2; t3 tk 1->0.5 = 0.5.
    assert float(pt.drop_hidden[0, 2].sum()) == pytest.approx(2.5)
    assert float(pt.drop_keep_hidden[0, 2].sum()) == pytest.approx(1.5)
    assert float(pt.drop_gate_loss[0, 2].sum()) == pytest.approx(2.0)
    # s1 -> s2 on t2: s1 resolved t2, so that drop (1,1,1)->(0,0,0) = 3 is a flip, not hidden; the only hidden
    # drop is t1 (jointly unresolved): FAIL_TO_PASS 1 -> 0 = 1.
    assert float(pt.drop_gate_loss[1, 2].sum()) == pytest.approx(3.0)
    assert float(pt.drop_hidden[1, 2].sum()) == pytest.approx(1.0)


def test_split_pairs_counts_on_validation_half(e10):
    rng = np.random.default_rng(0)
    r = (rng.random((5, 20)) < 0.5).astype(float)
    g = np.ones_like(r)
    tf = np.where(r == 1, 1.0, rng.random(r.shape))
    tk = np.where(r == 1, 1.0, rng.random(r.shape))
    m = _matrix(e10, r, g, tf, tk)
    pt = e10.pair_tensors(m)
    val = np.zeros(20, bool)
    val[:10] = True
    st = e10.split_pairs(m, pt, val, near_max_gain=2)
    rv = r[:, :10]
    assert np.array_equal(st["gains_v"], (1 - rv) @ rv.T)
    assert np.array_equal(st["losses_v"], rv @ (1 - rv).T)
    assert np.allclose(st["trm_v"], pt.drop_total[:, :, :10].sum(-1) / 10)
    rt = r[:, 10:]
    assert np.allclose(st["dpass_t"], ((1 - rt) @ rt.T - rt @ (1 - rt).T) / 10)
    assert not st["eligible"][np.arange(5), np.arange(5)].any()
    assert (st["net_v"][st["near"]] <= 2).all() and (st["net_v"][st["near"]] > 0).all()


def test_select_prefix_matches_floor_and_respects_order(e10):
    order = np.array([3, 0, 4, 1, 2])
    keep = e10.select_prefix(order, np.ones((1, 5)), 0.5)
    assert keep[0].tolist() == [True, False, False, True, False]  # first floor(2.5)=2 of the order: 3, 0
    w = np.array([[0.0, 1.0, 1.0, 2.0, 1.0]])
    keep = e10.select_prefix(order, w, 0.5)  # total 5, budget 2.5: 3 (w2) then 0 (w0) then 4 (w1) -> 3 > 2.5 stops
    assert keep[0].tolist() == [True, False, False, True, False]


def test_weighted_ranks_ones_and_duplication(e10):
    x = np.array([3.0, 1.0, 2.0, 2.0, 5.0])
    ranks = e10.weighted_ranks(x, np.ones((1, 5)))[0]
    assert ranks.tolist() == [3.5, 0.5, 2.0, 2.0, 4.5]  # midpoint ranks (0-based + 0.5), ties averaged
    w = np.array([[2.0, 1.0, 1.0, 1.0, 1.0]])
    dup = np.r_[x, x[0]]
    rd = e10.weighted_ranks(dup, np.ones((1, 6)))[0]
    assert pytest.approx(e10.weighted_ranks(x, w)[0][0]) == rd[0]


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
    assert pytest.approx(weighted, abs=1e-9) == dup
    assert -1 <= weighted <= 1


def test_bootstrap_weights_are_products_of_multiplicities(e10):
    w = e10.bootstrap_weights(6, 3, seed=7)
    assert w.shape == (4, 6, 6)
    assert np.all(w[0] == 1)
    rng = np.random.default_rng(7)
    m = rng.multinomial(6, np.full(6, 1 / 6), size=3)
    assert np.array_equal(w[1:], m[:, :, None] * m[:, None, :])


def test_binary_gate_rejects_fix3_break2_that_scalar_promotes(e10):
    # Incumbent solves tasks 0-1; candidate A fixes 2-4 and breaks 0-1 (net +1); candidate B fixes task 2 only (net +1).
    r = np.array([[1, 1, 0, 0, 0, 0], [0, 0, 1, 1, 1, 0], [1, 1, 1, 0, 0, 0]], float)
    g = np.ones_like(r)
    m = _matrix(e10, r, g, r, np.ones_like(r))
    pt = e10.pair_tensors(m)
    st = e10.split_pairs(m, pt, np.array([True] * 5 + [False]), near_max_gain=5)
    idx = np.flatnonzero(st["near"].ravel())
    pairs = [(int(st["inc"].ravel()[i]), int(st["cand"].ravel()[i])) for i in idx]
    assert (0, 1) in pairs and (0, 2) in pairs
    orders = e10.policy_orders(st, idx, e10.pair_hash(m.systems))
    first_s2 = pairs[orders["S2"][0]]
    assert first_s2 == (0, 2)  # binary non-regression ranks the zero-loss candidate first


def test_load_matrix_rejects_wrong_hash_and_reads_gated_factors(tmp_path, e10):
    rows = []
    for s in ("a", "b"):
        for t in ("x", "y"):
            gate = 0 if (s, t) == ("b", "y") else 1
            rows.append({"submission": s, "instance_id": t, "included": True, "common_cohort": True, "gate": gate,
                         "t_fix": None if gate == 0 else 0.5, "t_keep": None if gate == 0 else 1.0, "resolved": False})
    p = tmp_path / "cells.jsonl.gz"
    p.write_bytes(gzip.compress("\n".join(json.dumps(r) for r in rows).encode()))
    with pytest.raises(SystemExit):
        e10.load_matrix(p, expect_sha="0" * 64)
    m = e10.load_matrix(p, expect_sha=None)
    assert m.gf.tolist() == [[0.5, 0.5], [0.5, 0.0]] and m.g.tolist() == [[1, 1], [1, 0]]
