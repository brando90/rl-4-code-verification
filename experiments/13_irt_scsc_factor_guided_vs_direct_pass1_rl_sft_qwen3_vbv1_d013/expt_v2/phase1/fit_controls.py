"""Validate the actual observed conditional-risk pattern before interpreting Phase 1 fits."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import numpy as np
from scipy.special import expit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'prediction'))
from irt_v2 import conditional_counts, objective, START_SEEDS
from recovery_v2 import recover_pattern
from forecast_a3 import forecast_a3 as forecast_panel


def numerical_controls():
    """Fixed synthetic gradient and unpenalized likelihood-invariance controls."""
    rng = np.random.default_rng(1302151)
    n = np.full((4, 5), 8.); y = rng.binomial(8, .4, n.shape)
    features = rng.normal(size=(5, 2))
    x = np.r_[[-1.5, -.5, .5, 1.5], rng.normal(0, .2, 5), rng.normal(0, .1, 5), [.2, -.1]]
    loss, grad = objective(x, y, n, features)
    approx = []
    for i in range(len(x)):
        delta = np.zeros_like(x); delta[i] = 1e-5
        approx.append((objective(x+delta, y, n, features)[0]-objective(x-delta, y, n, features)[0])/2e-5)
    error = float(np.max(np.abs(grad - approx)))
    theta = np.linspace(-1.5, 1.5, 4); a = np.exp(rng.normal(0, .2, 5)); b = rng.normal(size=5)
    p = expit(a * (theta[:, None]-b))
    transformed = expit((a/2.3)*((2.3*theta+1.2)[:, None]-(2.3*b+1.2)))
    invariance = float(np.max(np.abs(p-transformed)))
    return {'status': 'PASS' if np.isfinite(loss) and np.isfinite(grad).all()
            and error <= 1e-5 and invariance <= 1e-12 else 'FAIL',
            'gradient_max_absolute_error': error, 'gradient_tolerance': 1e-5,
            'likelihood_probability_invariance_error': invariance, 'invariance_tolerance': 1e-12,
            'fixed_initializations': list(START_SEEDS), 'seed': 1302151}


def validate_history(history, shape):
    required = ('strict', 'q1', 'compile', 'honest', 'observed', 'policy_index', 'item_index')
    arrays = {k: np.asarray(history[k]) for k in required}
    n = len(arrays['strict'])
    if any(a.shape != (n,) for a in arrays.values()):
        raise ValueError('unaligned history')
    observed = arrays['observed']
    if observed.dtype != bool:
        raise ValueError('missingness must be an explicit Boolean mask')
    for name in ('strict', 'q1', 'compile', 'honest'):
        if not np.isin(arrays[name][observed], [0, 1]).all():
            raise ValueError('unmeasured value in observed history')
    for name, limit in zip(('policy_index', 'item_index'), shape):
        a = arrays[name]
        if not np.issubdtype(a.dtype, np.integer) or np.any((a < 0) | (a >= limit)):
            raise ValueError('invalid history index')
    return arrays


def pattern_controls(history, shape):
    arrays = validate_history(history, shape)
    counts = conditional_counts(arrays['q1'], arrays['compile'], arrays['honest'],
                                arrays['observed'], arrays['policy_index'], arrays['item_index'], shape)
    trials = np.zeros(shape, dtype=int)
    ix = arrays['observed']
    np.add.at(trials, (arrays['policy_index'][ix], arrays['item_index'][ix]), 1)
    patterns = [('M2', trials)] + [(f'Q{k+1}', n.astype(int)) for k, (_, n) in enumerate(counts)]
    results = {}
    for name, n in patterns:
        # Exactly this fold's trials, including zero cells; no repair, refill or
        # dense surrogate. Recovery generates labels, never reuses real labels.
        result = recover_pattern(n)
        result.update(pattern_sha256=hashlib.sha256(n.astype('<i8').tobytes()).hexdigest(),
                      shape=list(n.shape), zero_cells=int(np.sum(n == 0)), trials=int(n.sum()))
        results[name] = result
    nested = arrays['q1'].astype(bool) & arrays['compile'].astype(bool) & arrays['honest'].astype(bool)
    disagreements = int(np.sum(ix & (nested != arrays['strict'])))
    numeric = numerical_controls()
    return {'status': 'PASS' if numeric['status'] == 'PASS' and not disagreements
            and all(r['status'] == 'PASS' for r in results.values()) else 'FAIL',
            'patterns': results, 'numerical': numeric, 'chain_disagreements': disagreements,
            'observed_cells': int(ix.sum()), 'missing_cells': int((~ix).sum())}


def validated_forecast(**kwargs):
    controls = pattern_controls(kwargs['history'], (len(kwargs['policy_metadata']), len(kwargs['item_features'])))
    predictions, receipts = forecast_panel(**kwargs)
    for receipt in receipts.values():
        receipt['implementation_controls'] = controls
        receipt['admitted'] = receipt['admitted'] and controls['status'] == 'PASS'
    return predictions, receipts
