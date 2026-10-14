"""Prospective fixed-forecast A3 bounds; never fits a model or reads a data file."""
from __future__ import annotations

import itertools
import math
import numpy as np
from scipy.stats import pearsonr


def validate(y, p=None):
    y = np.asarray(y, float)
    if y.ndim != 1 or not len(y) or not np.all(np.isnan(y) | np.isin(y, [0, 1])):
        raise ValueError('labels must be binary or explicitly missing')
    if p is not None:
        p = np.asarray(p, float)
        if p.shape != y.shape or np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
            raise ValueError('fixed forecasts incomplete or invalid')
        return y, p
    return y


def linear_completions(y, coefficient):
    """Point and every nonnegative-weight resample share these extrema."""
    y = validate(y)
    a = np.asarray(coefficient, float)
    if a.shape != y.shape or np.any(~np.isfinite(a)):
        raise ValueError('invalid linear coefficients')
    missing = np.isnan(y)
    low, high = y.copy(), y.copy()
    low[missing] = (a[missing] < 0).astype(float)
    high[missing] = (a[missing] >= 0).astype(float)
    return low, high


def coefficients(p, metric, baseline=None):
    p = np.asarray(p, float)
    if p.ndim != 1 or np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError('invalid fixed forecasts')
    if metric == 'mean_bias':
        return -np.ones_like(p), p
    if metric == 'mean_absolute_error':
        return 1 - 2*p, p
    if metric == 'brier':
        return 1 - 2*p, p*p
    if metric == 'predicted_mean':
        return np.zeros_like(p), p
    if metric == 'observed_mean':
        return np.ones_like(p), np.zeros_like(p)
    if metric in ('log_loss', 'log_loss_contrast'):
        clipped = np.clip(p, 1e-12, 1-1e-12)
        a, b = np.log1p(-clipped)-np.log(clipped), -np.log1p(-clipped)
        if metric == 'log_loss_contrast':
            other = np.asarray(baseline, float)
            if other.shape != p.shape:
                raise ValueError('unpaired baseline')
            aa, bb = coefficients(other, 'log_loss')
            a, b = a-aa, b-bb
        return a, b
    raise ValueError('metric is not linear in binary target labels')


def bound_linear(y, a, b, groups, *, draws=10000, seed=1302031):
    """Exact completion ranges for a point mean and both bootstrap endpoints.

    Group draws match the frozen evaluation order/seed. Since every draw is a
    nonnegative weighted mean, the same completions attain the extrema of every
    draw; quantiles preserve this ordering. These are completion ranges, not
    confidence intervals for missingness or refitted parameter uncertainty.
    """
    y = validate(y); a, b = np.asarray(a, float), np.asarray(b, float)
    groups = np.asarray(groups)
    if groups.shape != y.shape or b.shape != y.shape or np.any(~np.isfinite(b)) or draws < 1:
        raise ValueError('invalid paired bootstrap inputs')
    low, high = linear_completions(y, a)
    values = np.stack((a*low+b, a*high+b))
    unique = np.unique(groups)
    indices = [np.flatnonzero(groups == g) for g in unique]
    boot = np.empty((2, draws)); rng = np.random.default_rng(seed)
    for draw in range(draws):
        ix = np.concatenate([indices[i] for i in rng.integers(0, len(indices), len(indices))])
        boot[:, draw] = values[:, ix].mean(axis=1)
    ci = np.quantile(boot, [.025, .975], axis=1)
    return {'minimum': float(values[0].mean()), 'maximum': float(values[1].mean()),
            'bootstrap_lower_endpoint_range': ci[0].tolist(),
            'bootstrap_upper_endpoint_range': ci[1].tolist(),
            'exact': True, 'draws': draws, 'seed': seed,
            'groups': len(unique), 'declared_cells': len(y),
            'excluded_cells': int(np.isnan(y).sum())}, (low, high)


def bound_policy_pearson(y, p, policies, *, limit=2**20):
    """Exact finite search over per-policy missing-success totals, when bounded."""
    y, p = validate(y, p); policies = np.asarray(policies)
    if policies.shape != y.shape:
        raise ValueError('unpaired policy identities')
    unique = np.unique(policies)
    index = [np.flatnonzero(policies == policy) for policy in unique]
    counts = [int(np.isnan(y[ix]).sum()) for ix in index]
    total = math.prod(n+1 for n in counts)
    predicted = np.array([p[ix].mean() for ix in index])
    if len(unique) < 2 or np.ptp(predicted) == 0:
        return {'minimum': None, 'maximum': None, 'undefined_possible': True,
                'exact': True, 'configurations': total}
    if total > limit:
        return {'minimum': -1., 'maximum': 1., 'undefined_possible': True,
                'exact': False, 'configurations': total,
                'reason': 'conservative outer bound; cannot certify admission'}
    known = np.array([np.nansum(y[ix]) for ix in index])
    denominators = np.array([len(ix) for ix in index])
    minimum = maximum = None; undefined = False
    witnesses = {}
    for completion in itertools.product(*(range(n+1) for n in counts)):
        observed = (known + completion) / denominators
        if np.ptp(observed) == 0:
            undefined = True
            continue
        rho = float(pearsonr(observed, predicted).statistic)
        if minimum is None or rho < minimum:
            minimum = rho; witnesses['minimum_missing_success_counts'] = list(completion)
        if maximum is None or rho > maximum:
            maximum = rho; witnesses['maximum_missing_success_counts'] = list(completion)
    return {'minimum': minimum, 'maximum': maximum, 'undefined_possible': undefined,
            'exact': True, 'configurations': total, 'policy_order': unique.tolist(), **witnesses}
