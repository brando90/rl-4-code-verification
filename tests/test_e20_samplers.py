"""TLDR: Unit tests for experiment 20's prompt samplers: uniform permutation streams without replacement and shared across arms A/B, the static filter's eligibility, DAPO filtering and budget accounting, weighted sampling without replacement, the IRT-online selection weights, the sequential EAP update and checkpoint round trips."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/expt_v1/samplers_e20.py"
spec = importlib.util.spec_from_file_location("samplers_e20", SRC)
S = importlib.util.module_from_spec(spec)
sys.modules["samplers_e20"] = S
spec.loader.exec_module(S)

TASKS = [f"t{i:03d}" for i in range(40)]
NODES = np.linspace(-12, 12, 1201)


def test_uniform_is_without_replacement_and_shared_between_arms():
    a, b = S.Uniform(TASKS, seed=7), S.Uniform(TASKS, seed=7)
    drawn = [a.next_groups(16) for _ in range(5)]  # 80 draws over 40 tasks: two full permutations
    flat = [t for g in drawn for t in g]
    assert sorted(flat[:40]) == sorted(TASKS) and sorted(flat[40:]) == sorted(TASKS)
    assert [b.next_groups(16) for _ in range(5)] == drawn  # arms A and B share the stream per seed
    assert S.Uniform(TASKS, seed=8).next_groups(16) != drawn[0]


def test_static_filter_uses_only_eligible_tasks_and_needs_16():
    k = {t: (i % 9) for i, t in enumerate(TASKS)}  # 0..8; eligible = 1..7
    s = S.StaticFilter(TASKS, seed=1, phase0_successes=k)
    eligible = {t for t in TASKS if 1 <= k[t] <= 7}
    assert set(t for _ in range(3) for t in s.next_groups(16)) <= eligible
    with pytest.raises(ValueError):
        S.StaticFilter(TASKS, seed=1, phase0_successes={t: 0 for t in TASKS})


def test_dapo_filter_and_budget():
    e = S.DynamicDAPO(TASKS, seed=3, rollout_budget=300)
    batch = e.next_groups(16)
    e.register_generated(16 * 8)
    keep = e.filter_active(batch, [0, 8, 3, 1, 7, 0, 0, 8, 4, 4, 0, 8, 2, 0, 5, 8])
    assert keep == [2, 3, 4, 8, 9, 12, 14]
    assert e.budget.kept_groups == 7 and e.budget.dropped_groups == 9 and not e.budget.exhausted
    e.register_generated(16 * 8)
    assert not e.budget.exhausted
    e.register_generated(16 * 8)
    assert e.budget.exhausted and e.budget.generated == 384


def test_weighted_sample_without_replacement_matches_weights():
    rng = np.random.default_rng(0)
    w = np.array([0.0, 1.0, 1.0, 8.0])
    counts = np.zeros(4)
    for _ in range(4000):
        counts[S.weighted_sample_without_replacement(rng, w, 1)] += 1
    assert counts[0] == 0 and abs(counts[3] / 4000 - 0.8) < 0.03
    with pytest.raises(ValueError):
        S.weighted_sample_without_replacement(rng, w, 4)


def test_eap_update_moves_toward_the_evidence():
    a, d = np.ones(10), np.zeros(10)
    theta_hi, sd_hi = S.eap_update(0.0, 1.0, np.full(10, 8), np.full(10, 8), a, d, NODES)
    theta_lo, _ = S.eap_update(0.0, 1.0, np.zeros(10), np.full(10, 8), a, d, NODES)
    theta_mid, sd_mid = S.eap_update(0.0, 1.0, np.full(10, 4), np.full(10, 8), a, d, NODES)
    assert theta_hi > 1.0 > -1.0 > theta_lo and abs(theta_mid) < 0.05 and 0 < sd_mid < sd_hi < 1.0


def test_irt_online_draws_by_information_and_updates_theta():
    rng = np.random.default_rng(1)
    a = np.exp(rng.normal(0, 0.3, 40))
    d = np.linspace(-6, 6, 40)
    items = S.IRTItems(TASKS, a, d)
    s = S.IRTOnline(TASKS, seed=5, items=items, theta0=0.0, theta0_sd=0.5, nodes=NODES)
    counts = np.zeros(40)
    for u in range(1, 31):
        g = s.next_groups(16)
        assert len(set(g)) == 16
        counts[[items.index[t] for t in g]] += 1
        assert sum(f["irt_draw"] for f in s.forecasts[-16:]) == 12
        # feed back outcomes consistent with the true ability 0: p = sigmoid(d)
        ks = [int(rng.binomial(8, expit(a[items.index[t]] * 0.0 + d[items.index[t]]))) for t in g]
        s.observe(u, g, ks, [8] * 16)
    informative = np.argsort(-(a**2 * expit(d) * (1 - expit(d))))[:10]
    assert counts[informative].mean() > counts.mean()  # mid-difficulty items are drawn more often
    assert abs(s.theta) < 0.75 and len(s.history) == 31
    f = s.forecasts[0]
    assert abs(f["p_active"] - S.forecast_active(f["p"])) < 1e-12


def test_state_round_trip_reproduces_the_stream():
    for make in (lambda: S.Uniform(TASKS, seed=2), lambda: S.DynamicDAPO(TASKS, seed=2),
                 lambda: S.IRTOnline(TASKS, seed=2, items=S.IRTItems(TASKS, np.ones(40), np.linspace(-3, 3, 40)), theta0=0.1, theta0_sd=0.4, nodes=NODES)):
        s1 = make()
        s1.next_groups(16)
        if isinstance(s1, S.IRTOnline):
            s1.observe(1, s1.drawn[-1], [3] * 16, [8] * 16)
        state = s1.state()
        s2 = make()
        s2.load_state(state)
        assert s1.next_groups(16) == s2.next_groups(16)
        if isinstance(s1, S.IRTOnline):
            assert s1.theta == s2.theta and s1.history == s2.history


def test_make_sampler_dispatch():
    assert S.make_sampler("A", TASKS, 1).next_groups(16) == S.make_sampler("B", TASKS, 1).next_groups(16)
    assert isinstance(S.make_sampler("E", TASKS, 1), S.DynamicDAPO)
    with pytest.raises(KeyError):
        S.make_sampler("Z", TASKS, 1)
