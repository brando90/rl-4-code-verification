"""Experiment 25 Night 6 (expt_v6): logged GRPO equals policy.grpo, schedules, job list, fits, bit packing."""
from collections import Counter
from copy import deepcopy
from importlib import import_module
import numpy as np
import pytest

torch = pytest.importorskip('torch')
base = 'experiments.25_checkpoint_reuse_for_rho_h_law.expt_v6'
n6 = import_module(f'{base}.night6')
a6 = import_module(f'{base}.analyze6')
p6 = import_module(f'{base}.policy6')
pol = import_module('experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2.policy')
from rl4cv.utility_model import Observation, fit_utility_model, RHO_H


def _model():
    m = n6.load_model(n6.NIGHT5, 'n1')
    ref = deepcopy(m).eval()
    for q in ref.parameters():
        q.requires_grad_(False)
    return m, ref


def test_logged_constant_schedule_is_bit_identical_to_policy_grpo():
    torch.set_num_threads(1)
    spec = n6.specs(n6.NIGHT5)[0]
    pool = n6.make_prompts(spec, 500, 13)
    ev = lambda m: {'w': float(m.head.weight.sum())}
    m1, r1 = _model()
    m2, r2 = _model()
    a = pol.grpo(m1, r1, pool, 3, {1, 3}, ev, 0, batch=16, group=8, lr=3e-4, kl_coef=0.1)
    b, log, _ = p6.grpo_logged(m2, r2, pool, 3, {1, 3}, ev, 0, batch=16, group=8, lr=3e-4, kl_coef=0.1)
    assert a[3]['w'] == b[3]['w'] and a[1]['w'] == b[1]['w'] and a[3]['last_train_kl'] == b[3]['last_train_kl']
    assert log['reward'].shape == (3, 16, 8) and np.allclose(log['advantage'].sum(2), 0, atol=1e-5) and set(log['lr']) == {3e-4}


def test_cosine_schedule_values():
    assert p6.lr_at('constant', 1.0, 50, 100) == 1.0
    assert p6.lr_at('cosine', 1.0, 1, 100) == 1.0
    assert p6.lr_at('cosine', 1.0, 51, 100) == pytest.approx(0.5)
    assert 0 <= p6.lr_at('cosine', 1.0, 100, 100) < 1e-3
    with pytest.raises(ValueError):
        p6.lr_at('wsd', 1.0, 1, 10)


def test_job_list_counts_and_disjoint_seeds():
    J = n6.jobs()
    assert len(J) == 492 and len({n6.job_name(j) for j in J}) == 492
    assert Counter(j['arm'] for j in J) == {'A': 192, 'pool': 144, 'B': 84, 'cosL': 24, 'cosS': 48}
    cell = Counter((j['scale'], j['env'], j['seed']) for j in J if j['arm'] != 'cosS' or True)
    assert max(cell.values()) == 1                                   # no seed reused inside a (scale, env)
    assert [j['stage'] for j in J][0] == 's1_main_n1_n3' and J[-1]['stage'] == 's7_main_n4'
    assert sum(j['steps'] for j in J if j['arm'] == 'B' and j['scale'] == 'n1' and j['env'] == 'e00') == 1200


def test_pack_roundtrip():
    bits = np.random.default_rng(0).random(n6.TARGET_N) < .3
    assert (n6.unpack(n6.pack(bits)) == bits).all()


def test_reproduces_night5_first_checkpoint(tmp_path):
    j = {'stage': 't', 'arm': 'A', 'scale': 'n1', 'env': 'e00', 'seed': 0, 'steps': 25, 'schedule': 'constant', 'horizon': 25}
    name, _ = n6.run_job(j, tmp_path / 'r', tmp_path / 'l', tmp_path / 'c')
    mine = n6.read(tmp_path / 'r' / f'{name}.json')['rows'][0]
    old = n6.read(n6.NIGHT5 / 'main_n1_e00_seed0.json')['rows'][0]
    assert old['step'] == mine['step'] == 25 and mine['utility'] == old['utility'] and mine['lr_fraction'] == 1.0
    assert mine['n_groups_roll'] == 400 and mine['rho_roll'] > 0


def test_fast_law_matches_utility_model():
    rng = np.random.default_rng(1)
    obs = [Observation(float(p), f'e{j}', float(b), float(rng.normal()), float(np.exp(rng.normal())), float(rng.uniform()))
           for p in (100, 400, 1600) for j in range(5) for b in (1000., 2000., 4000.)]
    obs = [Observation(o.scale, o.env, o.budget, o.utility, *(next(x for x in obs if x.scale == o.scale and x.env == o.env).rho,
                                                              next(x for x in obs if x.scale == o.scale and x.env == o.env).H)) for o in obs]
    fast = a6.fit_law(obs, (100., 1600.))
    ref = fit_utility_model(obs, RHO_H, C0=fast.c0, ref_scales=(100., 1600.))
    assert np.allclose(fast.beta, ref.beta, atol=1e-9)
    assert all(fast.predict_obs(o) == pytest.approx(ref.predict_obs(o), abs=1e-9) for o in obs)


def test_curve_fits_recover_truth():
    C = a6.BUDGET
    u = 0.08 * C / (C + 40 * a6.TOK)
    a, c0, sse = a6.saturating_fit(C, u)
    assert a == pytest.approx(0.08, rel=0.1) and sse < 1e-5
    p = a6.sigmoid_fit(C, u)
    assert a6.sigmoid_predict(p, C[-1]) == pytest.approx(u[-1], abs=2e-3)
