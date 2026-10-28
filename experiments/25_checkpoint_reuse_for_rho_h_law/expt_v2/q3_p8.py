"""TLDR: Q3 (P8) on CPU: fit a sigmoid and the Eq. 7 saturating form on 10-50% of each public RL reward curve (Snowball sync, async, 5.7T; Delphi D1-D4 logs), score MAE over 50-100% divided by the curve's range, as frozen in PROTOCOL addendum A."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares


def sigmoid(t, A, log_tmid, B):
    return A / (1.0 + np.exp(-(np.log(t) - log_tmid) / B))


def fit_sigmoid(t, y, ymax, nsteps):
    best = None
    for lt0 in np.linspace(0, np.log(2 * nsteps), 7):
        for B0 in (0.3, 1.0, 3.0):
            for A0 in (0.5 * ymax, ymax, 1.4 * ymax):
                lo = [0.0, 0.0, 0.1]
                hi = [1.5 * max(ymax, 1e-9), np.log(2 * nsteps), 5.0]
                p0 = np.clip([A0, lt0, B0], lo, hi)
                try:
                    r = least_squares(lambda p: sigmoid(t, *p) - y, p0, bounds=(lo, hi))
                except Exception:
                    continue
                if best is None or r.cost < best.cost:
                    best = r
    return best.x


def fit_sat(t, y):
    best = None
    for t0 in np.exp(np.linspace(np.log(0.5), np.log(1e4), 400)):
        f = t / (t + t0)
        a = float(np.dot(f, y) / np.dot(f, f))
        c = float(np.sum((a * f - y) ** 2))
        if best is None or c < best[0]:
            best = (c, a, t0)
    return best[1], best[2]


def evaluate(steps, y, shift=False):
    steps = np.asarray(steps, float)
    y = np.asarray(y, float)
    if shift:  # Delphi logs: raw reward in [-1, 1], so the frozen A in [0, 1.5 max] needs a shift to the observed minimum (deviation, logged)
        y = y - y.min()
    o = np.argsort(steps)
    steps, y = steps[o], y[o]
    n = len(steps)
    last = steps.max()
    rng = float(y.max() - y.min())
    fit = (steps >= 0.1 * last) & (steps <= 0.5 * last)
    test = steps > 0.5 * last
    if fit.sum() < 4 or test.sum() < 4 or rng <= 0:
        return None
    t, ft = steps[fit], y[fit]
    p = fit_sigmoid(t, ft, float(y.max()), last)
    a, t0 = fit_sat(t, ft)
    mae_sig = float(np.mean(np.abs(sigmoid(steps[test], *p) - y[test]))) / rng
    mae_sat = float(np.mean(np.abs(a * steps[test] / (steps[test] + t0) - y[test]))) / rng
    mae_last = float(np.mean(np.abs(np.mean(ft[-5:]) - y[test]))) / rng
    return {'n_steps': int(n), 'last_step': int(last), 'n_fit': int(fit.sum()), 'n_test': int(test.sum()), 'range': rng,
            'mae_over_range_sigmoid': mae_sig, 'mae_over_range_eq7_saturating': mae_sat, 'mae_over_range_flat_last5_baseline': mae_last,
            'sigmoid_params': [float(x) for x in p], 'sat_params': [a, t0], 'sigmoid_pass_le_0.10': mae_sig <= 0.10,
            'mean_fit_window': float(ft.mean()), 'mean_test_window': float(y[test].mean())}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--snow', required=True)
    ap.add_argument('--d-dir', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    rows = json.loads(Path(a.snow).read_text())['rows']
    byarm = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        byarm[r['arm']][r['domain']][r['step']] = r['mean_reward']
    out = {'blend': {}, 'per_domain': {}, 'delphi_D': {}}
    for arm, doms in byarm.items():
        stepvals = defaultdict(list)
        for d, s in doms.items():
            for k, v in s.items():
                stepvals[k].append(v)
        steps = sorted(stepvals)
        y = [float(np.mean(stepvals[k])) for k in steps]
        res = evaluate(steps, y)
        if res:
            res['mean_domains_per_step'] = float(np.mean([len(stepvals[k]) for k in steps]))
            res['n_domains_total'] = len(doms)
        out['blend'][arm] = res
        for d, s in doms.items():
            if len(s) >= 40:
                out['per_domain'][f'{arm}|{d}'] = evaluate(list(s.keys()), list(s.values()))
    for p in sorted(Path(a.d_dir).glob('*/train_steps.csv')):
        rr = list(csv.DictReader(p.open()))
        out['delphi_D'][p.parent.name] = evaluate([float(r['step']) for r in rr], [float(r['reward/avg_raw_reward']) for r in rr], shift=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    for k, v in out['blend'].items():
        print('BLEND', k, v and {x: round(y, 3) if isinstance(y, float) else y for x, y in v.items() if x.startswith('mae') or x in ('n_steps', 'range', 'mean_domains_per_step')})
    for k, v in out['delphi_D'].items():
        print('DELPHI', k, v and {x: round(y, 3) if isinstance(y, float) else y for x, y in v.items() if x.startswith('mae') or x in ('n_steps', 'range')})
    pd = [v for v in out['per_domain'].values() if v]
    print('per-domain curves', len(pd), 'sigmoid pass', sum(v['sigmoid_pass_le_0.10'] for v in pd),
          'sigmoid better than eq7', sum(v['mae_over_range_sigmoid'] < v['mae_over_range_eq7_saturating'] for v in pd),
          'sigmoid better than flat', sum(v['mae_over_range_sigmoid'] < v['mae_over_range_flat_last5_baseline'] for v in pd))


if __name__ == '__main__':
    main()
