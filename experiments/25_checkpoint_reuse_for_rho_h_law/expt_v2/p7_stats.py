"""TLDR: P7 (Q2) from the per-checkpoint measurement files: for the D-at-fixed-N ladder (3.4B, 5 token budgets) and the N ladder (3.4B, 9.7B, 25B), per environment over measurable cells only, Spearman of log rho and H against the ladder axis and a leave-largest-out linear fit in log axis; below-bar cells are listed, never fitted."""
import json
import math
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parent / 'results'
LADDERS = {
    'D_at_fixed_N_3.4B': {'axis': 'tokens_B', 'cells': [('q2b_3e19', 1.4), ('q2b_9e19', 4.2), ('q2b_2e20', 8.3), ('q2b_3e20', 13.9), ('q1_3p4b_base', 46.3)]},
    'N_at_compute_optimal_D': {'axis': 'params_B', 'cells': [('q1_3p4b_base', 3.4), ('q1_9p7b_base', 9.7), ('q2a_25b', 25.0)]},
}
BAR = 0.2


def rankdata(x):
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind='mergesort')
    ranks = np.empty(len(x))
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(a, b):
    ra = rankdata(a)
    rb = rankdata(b)
    return float(np.corrcoef(ra, rb)[0, 1]) if np.std(ra) > 0 and np.std(rb) > 0 else None


def main():
    out = {}
    for name, lad in LADDERS.items():
        meas = {}
        for tag, x in lad['cells']:
            f = R / f'{tag}_measure.json'
            meas[tag] = (x, json.loads(f.read_text())['envs'] if f.exists() else None)
        envs = sorted({e for _, (x, m) in meas.items() if m for e in m})
        res = {'axis': lad['axis'], 'cells_not_run': [t for t, (x, m) in meas.items() if m is None], 'envs': {}}
        for e in envs:
            cells = [(t, x, m[e]) for t, (x, m) in meas.items() if m and e in m]
            below = [{'cell': t, 'q_mixed': round(v['q_mixed_empirical'], 3)} for t, x, v in cells if v['q_mixed_empirical'] < BAR]
            ok = [(t, x, v) for t, x, v in cells if v['q_mixed_empirical'] >= BAR]
            r = {'n_cells_run': len(cells), 'n_measurable': len(ok), 'below_bar_cells': below,
                 'q_mixed': {t: round(v['q_mixed_empirical'], 3) for t, x, v in cells}}
            if len(ok) >= 3:
                lx = np.log([x for _, x, _ in ok])
                for mname, fn, tol in (('log_rho', lambda v: math.log(max(v['rho'], 1e-9)), 0.25), ('H', lambda v: v['H'], 0.073)):
                    y = np.array([fn(v) for _, _, v in ok])
                    d = {'spearman': spearman(lx, y), 'values': [round(float(v), 4) for v in y]}
                    d['abs_spearman_ge_0.8'] = d['spearman'] is not None and abs(d['spearman']) >= 0.8
                    # leave-largest-out: needs the largest rung of the ladder measurable and >= 2 smaller measurable rungs
                    if ok[-1][0] == cells[-1][0] and len(ok) >= 3:
                        c = np.polyfit(lx[:-1], y[:-1], 1)
                        pred = float(np.polyval(c, lx[-1]))
                        d.update({'pred_largest': pred, 'obs_largest': float(y[-1]), 'abs_err': abs(pred - float(y[-1])), 'within_tol': abs(pred - float(y[-1])) <= tol, 'tol': tol})
                    else:
                        d['pred_largest'] = None
                    r[mname] = d
            res['envs'][e] = r
        out[name] = res
    (R / 'p7_q2.json').write_text(json.dumps(out, indent=1))
    for n, v in out.items():
        print(n, 'not run:', v['cells_not_run'])
        for e, r in v['envs'].items():
            print(' ', e, 'measurable', r['n_measurable'], '/', r['n_cells_run'], 'q', r['q_mixed'])
            for m in ('log_rho', 'H'):
                if m in r:
                    d = r[m]
                    print('    ', m, 'spearman', d['spearman'], 'pred_err', d.get('abs_err'), 'within', d.get('within_tol'))


if __name__ == '__main__':
    main()
