"""TLDR: tests for experiment 25 Stage 0 (checkpoint reuse): vectorized rho/H equals measure_environment, C0 grid recovers a known curve, P2 and P4 verdict logic."""
import importlib.util
import math
from pathlib import Path

import numpy as np

from rl4cv.experience import Response, measure_environment
from rl4cv.utility_model import Observation

PATH = Path(__file__).resolve().parents[1] / 'experiments/25_checkpoint_reuse_for_rho_h_law/expt_v1/stage0.py'
spec = importlib.util.spec_from_file_location('e25_stage0', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def synthetic_recs(seed=0, tasks=30, g=8):
    rng = np.random.default_rng(seed)
    recs = []
    for t in range(tasks):
        p = rng.uniform(0, 0.6)
        for i in range(g):
            recs.append({'task_id': f't{t:03d}', 'reward': float(rng.random() < p), 'generated_tokens': int(rng.integers(100, 900)),
                         'admitted': bool(rng.random() > 0.2)})
    return recs


def test_vectorized_metrics_match_measure_environment():
    recs = synthetic_recs()
    t, groups = m.task_arrays(recs)
    ref = measure_environment(groups)
    v = m.metrics_from_weights(t, np.ones((1, len(groups))))
    assert math.isclose(v['rho'][0], ref.rho, rel_tol=1e-9)
    assert math.isclose(v['H'][0], ref.H, rel_tol=1e-9)
    assert math.isclose(v['q_mixed'][0], ref.q_mixed_empirical, rel_tol=1e-9)
    assert math.isclose(v['admission'][0], ref.admission_rate, rel_tol=1e-9)


def test_bootstrap_weights_each_row_sums_to_n_tasks():
    W = m.boot_weights(25, draws=50, seed=1)
    assert W.shape == (50, 25) and np.all(W.sum(1) == 25)


def test_c0_grid_recovers_known_saturation():
    true_c0 = 512 * 100.0
    obs = []
    for s, scale in enumerate((1.0, 2.0, 4.0)):
        for e, (rho, h) in enumerate([(10, .2), (20, .4), (40, .5), (80, .9)]):
            for step in (25, 50, 100):
                c = 512.0 * step
                u = 0.01 * (c / (c + true_c0)) * (1 + 0.3 * math.log(rho) / 4 + h)
                obs.append(Observation(scale, f'e{e}', c, u, rho, h))
    model = m.fit_c0(obs, (1.0, 4.0), True)
    assert true_c0 / 1.5 < model.C0 < true_c0 * 1.5
    assert max(abs(model.predict_obs(o) - o.utility) for o in obs) < 1e-4


def test_p2_verdict_thresholds():
    block = {'x/FULL/gridC0': {'rmse_pp': 2.0, 'rank_acc': 0.6}, 'x/PREFIX50/gridC0': {'rmse_pp': 2.4, 'rank_acc': 0.55}}
    assert m.p2_verdict(block, 'x')['holds']
    block['x/PREFIX50/gridC0'] = {'rmse_pp': 2.6, 'rank_acc': 0.55}
    assert not m.p2_verdict(block, 'x')['holds']
    block['x/PREFIX50/gridC0'] = {'rmse_pp': 2.0, 'rank_acc': 0.45}
    assert not m.p2_verdict(block, 'x')['holds']


def test_p4_equivalence_verdicts():
    recs = {k: synthetic_recs(seed=s) for k, s in {'r50': 1, 'r100': 2, 'a': 3, 'b': 4, 'c': 5, 'd': 6}.items()}
    data = {k: (v, m.task_arrays(v)[0]) for k, v in recs.items()}
    W = m.boot_weights(30, draws=400, seed=3)
    out = m.p4(data, W, {'50': 'r50', '100': 'r100'}, {'50': ['a', 'b'], '100': ['c', 'd']})
    assert out['dH']['verdict'] in {'EQUIVALENT', 'NOT EQUIVALENT', 'INCONCLUSIVE'}
    lo, hi = out['dH']['pooled_ci95']
    assert lo < out['dH']['pooled_point'] < hi


def test_toy_data_are_complete():
    for night, path in m.NIGHTS.items():
        params, probes, cells = m.load_night(path)
        assert len(cells) == 16 * 4 * 3 * 3, night
        assert len({(s, e) for (s, e) in probes}) == 64
