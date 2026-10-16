"""Experiment 16 expt_v3: the known-MDP exact value matches Monte Carlo, and capped episodes are the failures."""

import sys
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v3"))

from known_mdp import A, N_STATES, TARGET, EnvSpec, exact_success, make_chain, rollout_groups  # noqa: E402


def _policy(chain, p):
    probs = np.tile(((1 - p) / (A - 1))[:, None], (1, A))
    probs[np.arange(N_STATES), chain.correct] = p
    return probs


@pytest.mark.parametrize("spec", [TARGET, EnvSpec("late", (12, 13, 14, 15), 0, 0.5)])
def test_exact_success_matches_monte_carlo(spec):
    chain = make_chain()
    rng = np.random.default_rng(0)
    p = rng.uniform(0.4, 0.9, N_STATES)
    exact = exact_success(torch.tensor(p, dtype=torch.float64), spec).numpy()
    ro = rollout_groups(_policy(chain, p), chain, spec, 8000, 8, rng)
    for k, s in enumerate(spec.starts):
        hit = ro["success"][ro["s0"] == s]
        assert abs(hit.mean() - exact[k]) < 4 * np.sqrt(exact[k] * (1 - exact[k]) / hit.size) + 1e-3


def test_capped_episodes_use_the_full_horizon():
    chain = make_chain()
    spec = EnvSpec("all", tuple(range(N_STATES)), 2, 0.0)
    ro = rollout_groups(_policy(chain, np.full(N_STATES, 0.6)), chain, spec, 500, 8, np.random.default_rng(1))
    horizon = np.array([spec.horizon(int(s)) for s in ro["s0"]])[:, None]
    assert np.all(ro["tokens"][ro["capped"]] == np.broadcast_to(horizon, ro["tokens"].shape)[ro["capped"]])
    assert np.all(ro["tokens"] == ro["sa_counts"].sum((2, 3)))
    assert np.array_equal(ro["capped"], ~ro["success"])
