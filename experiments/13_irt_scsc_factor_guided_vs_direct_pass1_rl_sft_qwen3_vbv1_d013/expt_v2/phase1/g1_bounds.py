"""Prospective fixed-forecast A3 bounds; never fits a model or reads a data file."""
from __future__ import annotations

import itertools
import math
import numpy as np
from scipy.stats import pearsonr
from scipy.stats import rankdata, spearmanr, kendalltau


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


def bound_policy_pearson(y, p, policies, *, limit=2**20, kind='pearson'):
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
        rho = float({'pearson': pearsonr, 'spearman': spearmanr, 'kendall': kendalltau}[kind](observed, predicted).statistic)
        if minimum is None or rho < minimum:
            minimum = rho; witnesses['minimum_missing_success_counts'] = list(completion)
        if maximum is None or rho > maximum:
            maximum = rho; witnesses['maximum_missing_success_counts'] = list(completion)
    return {'minimum': minimum, 'maximum': maximum, 'undefined_possible': undefined,
            'exact': True, 'configurations': total, 'policy_order': unique.tolist(), **witnesses}


def bound_binary_association(y, p, metric):
    """Exact point extrema by missing-positive count and ordered score sums.

    For fixed total positives, each metric is monotone in the positive score
    (or average-rank) sum. Ties use average ranks, matching the frozen evaluator.
    """
    y, p = validate(y, p)
    if metric not in ('auc', 'pearson', 'spearman', 'kendall'):
        raise ValueError('unsupported association')
    n = len(y); missing = np.isnan(y); known_positive = y == 1
    scores = p if metric == 'pearson' else rankdata(p)
    ordered = np.sort(scores[missing]); cumulative = np.r_[0., np.cumsum(ordered)]
    base = float(scores[known_positive].sum()); known = int(known_positive.sum())
    _, ties = np.unique(p, return_counts=True)
    untied_pairs = (n*(n-1) - np.sum(ties*(ties-1))) / 2
    values = []; undefined = False
    for k in range(len(ordered)+1):
        positive = known + k
        if positive == 0 or positive == n or (metric != 'auc' and np.ptp(p) == 0):
            undefined = True; continue
        low = base + cumulative[k]
        high = base + cumulative[-1] - cumulative[len(ordered)-k]
        for score_sum in (low, high):
            if metric == 'auc':
                value = (score_sum-positive*(positive+1)/2)/(positive*(n-positive))
            elif metric == 'kendall':
                value = (2*score_sum-positive*(n+1))/math.sqrt(positive*(n-positive)*untied_pairs)
            else:
                denominator = math.sqrt(positive*(n-positive)/n * np.sum((scores-scores.mean())**2))
                value = (score_sum-positive*scores.mean())/denominator
            values.append(float(np.clip(value, 0 if metric == 'auc' else -1, 1)))
    return {'minimum': min(values) if values else None, 'maximum': max(values) if values else None,
            'undefined_possible': undefined, 'exact': True,
            'missing_positive_counts': len(ordered)+1}


def bound_association_interval(y, p, groups, metric, *, draws=10000, seed=1302031):
    """Outer bootstrap-endpoint bounds, preserving fixed original-cell labels.

    Repeated copies of a missing cell may vary independently only in the bounding
    relaxation. This enlarges the feasible set; it is never reported as exact.
    If defined resamples can depend on completion, full metric-range endpoint
    bounds avoid claiming a quantile bound across different retained draw sets.
    """
    y, p = validate(y, p); groups = np.asarray(groups)
    if groups.shape != y.shape or draws < 1:
        raise ValueError('invalid grouped association input')
    result = bound_binary_association(y, p, metric)
    indices = [np.flatnonzero(groups == g) for g in np.unique(groups)]
    rng = np.random.default_rng(seed); lows = []; highs = []; ambiguous = False
    for _ in range(draws):
        ix = np.concatenate([indices[i] for i in rng.integers(0, len(indices), len(indices))])
        b = bound_binary_association(y[ix], p[ix], metric)
        if b['undefined_possible'] and np.isnan(y[ix]).any():
            ambiguous = True; break
        if b['minimum'] is not None:
            lows.append(b['minimum']); highs.append(b['maximum'])
    floor = 0. if metric == 'auc' else -1.
    if ambiguous:
        lower = upper = [floor, 1.]
    elif lows:
        q = np.quantile([lows, highs], [.025, .975], axis=1)
        lower, upper = q[0].tolist(), q[1].tolist()
    else:
        lower = upper = [None, None]
    return {**result, 'bootstrap_lower_endpoint_range': lower,
            'bootstrap_upper_endpoint_range': upper, 'bootstrap_bounds_exact': not np.isnan(y).any(),
            'bootstrap_bound_method': 'full range if completion changes defined draws; otherwise repeated-cell relaxation',
            'completion_dependent_defined_draws': ambiguous, 'draws': draws, 'seed': seed}


def assess_g1_a3(y, predictions, groups, policies, *, implementation_admitted, draws=10000):
    """Apply the frozen G1 criteria to fixed forecasts at every held-out completion."""
    y = validate(y)
    required = ('selected', 'M0', 'M1', 'M2')
    missing = [name for name in required if name not in predictions
               or np.asarray(predictions[name]).shape != y.shape
               or not np.isfinite(predictions[name]).all()]
    metrics = {}; contrasts = {}
    for name, p in predictions.items():
        if p is None or np.asarray(p).shape != y.shape or not np.isfinite(p).all():
            metrics[name] = {'status': 'UNAVAILABLE'}; continue
        validate(y, p)
        metrics[name] = {m: bound_linear(y, *coefficients(p, m), groups, draws=draws)[0]
                        for m in ('log_loss', 'mean_bias', 'mean_absolute_error', 'brier',
                                  'observed_mean', 'predicted_mean')}
        metrics[name].update({m: bound_association_interval(y, p, groups, m, draws=draws)
                             for m in ('auc', 'pearson', 'spearman', 'kendall')})
        for kind in ('pearson', 'spearman', 'kendall'):
            metrics[name]['policy_'+kind] = {
                **bound_policy_pearson(y, p, policies, kind=kind),
                'bootstrap_lower_endpoint_range': [-1., 1.],
                'bootstrap_upper_endpoint_range': [-1., 1.],
                'bootstrap_bounds_exact': False,
                'bootstrap_bound_method': 'conservative full correlation range; point bounds gate only'}
        metrics[name]['policies'] = len(np.unique(policies))
        bins = np.minimum((np.asarray(p)*10).astype(int), 9)
        metrics[name]['calibration_bins'] = []
        for bin_id in np.unique(bins):
            ix = bins == bin_id
            metrics[name]['calibration_bins'].append({'bin': int(bin_id), 'cells': int(ix.sum()),
                'groups': len(np.unique(np.asarray(groups)[ix])),
                'predicted_mean': float(np.asarray(p)[ix].mean()),
                'observed_mean': [float(np.nansum(y[ix])/ix.sum()),
                                  float((np.nansum(y[ix])+np.isnan(y[ix]).sum())/ix.sum())]})
    if missing:
        return {'status': 'INCONCLUSIVE', 'missing_required_models': missing, 'disable_arm_C': True,
                'metrics':metrics,'paired_log_loss_contrasts':{},'declared_cells':len(y),
                'excluded_cells':int(np.isnan(y).sum()),'implementation_admitted':bool(implementation_admitted),
                'fit_repeated_per_completion':False,'threshold_source':'PROTOCOL section 4; A3 admission record'}
    selected = predictions['selected']
    for baseline in ('M0', 'M1'):
        contrasts[baseline] = bound_linear(y, *coefficients(selected, 'log_loss_contrast', predictions[baseline]),
                                          groups, draws=draws)[0]
    rho = metrics['selected']['policy_pearson']; bias = metrics['selected']['mean_bias']
    # Point associations must all be defined, as in PROTOCOL section 4.
    undefined = any(metrics['selected'][m]['undefined_possible']
                    for m in ('auc', 'pearson', 'spearman', 'kendall', 'policy_pearson'))
    passed = (implementation_admitted and not undefined and rho['exact'] and rho['minimum'] >= .8
              and all(c['bootstrap_upper_endpoint_range'][1] < 0 for c in contrasts.values())
              and bias['bootstrap_lower_endpoint_range'][1] <= 0
              and bias['bootstrap_upper_endpoint_range'][0] >= 0)
    failed = (not implementation_admitted
              or (rho['exact'] and rho['maximum'] is not None and rho['maximum'] < .8)
              or any(c['bootstrap_upper_endpoint_range'][0] >= 0 for c in contrasts.values())
              or bias['bootstrap_lower_endpoint_range'][0] > 0
              or bias['bootstrap_upper_endpoint_range'][1] < 0)
    status = 'PASS' if passed else 'FAIL' if failed else 'INCONCLUSIVE'
    return {'status': status, 'disable_arm_C': status != 'PASS', 'metrics': metrics,
            'paired_log_loss_contrasts': contrasts, 'implementation_admitted': bool(implementation_admitted),
            'declared_cells': len(y), 'excluded_cells': int(np.isnan(y).sum()),
            'fit_repeated_per_completion': False, 'threshold_source': 'PROTOCOL section 4; A3 admission record'}
