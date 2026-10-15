"""Experiment 16: GINC-style generator and exact verifier (numpy only, no torch)."""

import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "16_toy_env_generation_ginc_hmm_rho_h_law" / "expt_v1"))

from ginc_toy import V, EnvSpec, make_concept, make_prompts, next_symbol_dist, sample_sequences  # noqa: E402

from rl4cv.experience import Response, measure_environment  # noqa: E402


def brute_force_next(c, x):
    """p(x_{l+1} | x_{1:l}) by summing over every hidden path."""
    l = len(x)
    joint = np.zeros(V)
    for h in itertools.product(range(c.S), repeat=l):
        p = c.pi[h[0]] * c.B[h[0], x[0]]
        for t in range(1, l):
            p *= c.T[h[t - 1], h[t]] * c.B[h[t], x[t]]
        joint += p * (c.T[h[-1]] @ c.B)
    return joint / joint.sum()


def test_forward_matches_brute_force():
    c = make_concept(3, 4.0, seed=5)
    rng = np.random.default_rng(0)
    x = sample_sequences(c, 4, 5, rng)
    fast = next_symbol_dist(c, x)
    for i in range(4):
        np.testing.assert_allclose(fast[i], brute_force_next(c, x[i]), rtol=1e-9, atol=1e-12)


def test_sampler_matches_emission_marginal():
    c = make_concept(4, 2.0, seed=1)
    x = sample_sequences(c, 50_000, 1, np.random.default_rng(1))
    empirical = np.bincount(x[:, 0], minlength=V) / x.shape[0]
    np.testing.assert_allclose(empirical, c.pi @ c.B, atol=0.01)


def test_prompts_are_deterministic_and_labels_are_bayes_argmax():
    spec = EnvSpec("t", 4, 4.0, 3, 6)
    a, b = make_prompts(spec, 200, seed=3), make_prompts(spec, 200, seed=3)
    assert (a.x == b.x).all() and (a.y == b.y).all()
    assert a.x.shape == (200, 6) and a.y.min() >= 0 and a.y.max() < V
    assert ((a.bayes_acc > 0) & (a.bayes_acc <= 1)).all()


def test_rho_h_plumbing_for_one_token_binary_groups():
    groups = [[Response(r, 1, True) for r in row] for row in ([1, 0, 0, 0], [1, 1, 0, 0], [0, 0, 0, 0])]
    m = measure_environment(groups)
    assert m.q_mixed_empirical == 2 / 3
    assert 0 < m.H < 1 and m.rho > 0
