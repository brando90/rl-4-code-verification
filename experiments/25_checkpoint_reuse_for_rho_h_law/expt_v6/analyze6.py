"""Night 6 analysis: P1 (dense versus independent), P2 (prefix extrapolation), P3 (rolling rho, H), P5 (schedule control),
variance decomposition. Definitions are frozen in PROTOCOL.md before any Night 6 outcome is read.

  python -m experiments.25_checkpoint_reuse_for_rho_h_law.expt_v6.analyze6 --results <dir> --out <dir> [--draws 2000]
"""
import argparse
import itertools
import json
from collections import defaultdict
from importlib import import_module
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from rl4cv.utility_model import Observation, fit_utility_model, pairwise_rank_accuracy, RHO_H
from . import night6 as n6

K = n6.K
STEP_OF = n6.CHECKPOINT_STEPS                     # 25 .. 400
TOK = n6.BATCH * n6.GROUP * K                      # tokens per step (512)
BUDGET = np.array([s * TOK for s in STEP_OF], float)
CIDX = {s: i for i, s in enumerate(STEP_OF)}
C0_GRID = np.exp(np.linspace(np.log(10), np.log(4000), 41)) * TOK   # tokens
C_MAX = BUDGET[-1]
POOL_ENVS = n6.POOL_ENVS


# ------------------------------------------------------------------------------------------------- data

class Data:
    def __init__(self, results, night5=n6.NIGHT5):
        self.meta = {}
        self.runs = []
        for p in sorted(Path(results).glob('*.json')):
            d = n6.read(p)
            d['key'] = (d['arm'], d['scale'], d['env'], d['schedule'], d['horizon'])
            self.runs.append(d)
        scales = sorted({r['scale'] for r in self.runs})
        self.params = {s: n6.read(night5 / f'{s}_meta.json')['n_params'] for s in n6.ALL_SCALES}
        self.start = {s: (np.array(n6.read(night5 / f'{s}_meta.json')['start_target']['token_hits']) == K).astype(np.int8) for s in n6.ALL_SCALES}
        self.probes = {(s, r['env']): r for s in n6.ALL_SCALES for r in n6.read(night5 / f'{s}_probe.json')}
        self.envs = [s.name for s in n6.specs(night5)]
        self.ref = (self.params['n1'], self.params['n3'])
        R = len(self.runs)
        self.G = np.zeros((R, len(STEP_OF), n6.TARGET_N), np.float32)
        self.valid = np.zeros((R, len(STEP_OF)), bool)
        for i, r in enumerate(self.runs):
            for row in r['rows']:
                j = CIDX[row['step']]
                self.G[i, j] = n6.unpack(row['joint_bits']).astype(np.int8) - self.start[r['scale']]
                self.valid[i, j] = True
        self.groups = defaultdict(list)
        for i, r in enumerate(self.runs):
            self.groups[r['key']].append(i)
        self.groups = {k: np.array(v) for k, v in self.groups.items()}
        self.seed = np.array([r['seed'] for r in self.runs])

    def U(self, w=None):
        w = np.full(n6.TARGET_N, 1 / n6.TARGET_N, np.float32) if w is None else w.astype(np.float32)
        return (self.G @ w).astype(float)                       # runs x checkpoints

    def has(self, key, n):
        return key in self.groups and len(self.groups[key]) >= n


def identity_map(data):
    return dict(data.groups)


def boot_map(data, rng):
    """Resample runs with replacement inside every (arm, scale, env, schedule, horizon) group."""
    return {k: v[rng.integers(len(v), size=len(v))] for k, v in data.groups.items()}


def boot_map_seeds_per_scale(data, rng):
    """Night 4/5 style for the main matrix: one seed multiset per scale shared across environments (A runs)."""
    seed_map = {}
    out = {}
    for k, v in data.groups.items():
        if k[0] != 'A':
            out[k] = v[rng.integers(len(v), size=len(v))]
            continue
        sm = seed_map.setdefault(k[1], rng.integers(len(v), size=len(v)))
        out[k] = v[sm % len(v)]
    return out


# ------------------------------------------------------------------------------------------------- fits

def saturating_fit(C, u):
    """U = a*C/(C+C0): grid over C0 (tokens), closed-form a; returns (a, C0, sse)."""
    best = None
    for c0 in C0_GRID:
        s = C / (C + c0)
        a = float(s @ u / (s @ s))
        sse = float(((a * s - u) ** 2).sum())
        if best is None or sse < best[2]:
            best = (a, float(c0), sse)
    return best


def sigmoid_fit(C, u):
    """U = A / (1 + exp(-(log C - log Cmid)/B)); A in [-0.2, 0.3], log Cmid in log(10..4000 steps), B in [0.1, 5]."""
    lc = np.log(C)
    lo = [-0.2, np.log(10 * TOK), 0.1]
    hi = [0.3, np.log(4000 * TOK), 5.0]
    best = None
    for A0, m0, B0 in itertools.product((np.clip(u.max(), -0.19, 0.29), np.clip(u[-1], -0.19, 0.29)), (np.log(100 * TOK), np.log(1000 * TOK)), (0.5, 2.0)):
        f = lambda p: p[0] / (1 + np.exp(-(lc - p[1]) / p[2])) - u
        res = least_squares(f, [A0, m0, B0], bounds=(lo, hi))
        if best is None or res.cost < best.cost:
            best = res
    return best.x


def sigmoid_predict(p, C):
    return p[0] / (1 + np.exp(-(np.log(C) - p[1]) / p[2]))


class FastLaw:
    """Eq. 7 (same design and OLS as rl4cv.utility_model.fit_utility_model), vectorized for bootstrap loops."""
    def __init__(self, beta, c0, ref, z):
        self.beta, self.c0, self.ref, self.z = beta, c0, ref, z

    def row(self, scale, budget, rho, H):
        s = budget / (budget + self.c0)
        xn = np.log(scale / self.ref[0]) / np.log(self.ref[1] / self.ref[0])
        return np.array([1.0, xn, s, s * (np.log(rho) - self.z[0]) / self.z[1], s * (H - self.z[2]) / self.z[3]])

    def predict(self, scale, budget, rho, H):
        return float(self.row(scale, budget, rho, H) @ self.beta)

    def predict_obs(self, o):
        return self.predict(o.scale, o.budget, o.rho, o.H)


def fit_law(obs, ref):
    """Eq. 7 OLS with C0 chosen from the grid by training RMSE (same rule for prefix and full fits)."""
    train = [o for o in obs if o.budget > 0]
    cells = {}
    for o in train:
        cells[o.scale, o.env] = (o.rho, o.H)
    lr = np.log([v[0] for v in cells.values()])
    hh = np.array([v[1] for v in cells.values()])
    z = (float(lr.mean()), float(lr.std()) or 1.0, float(hh.mean()), float(hh.std()) or 1.0)
    B = np.array([o.budget for o in train])
    u = np.array([o.utility for o in train])
    xn = np.array([np.log(o.scale / ref[0]) / np.log(ref[1] / ref[0]) for o in train])
    zr = (np.log([o.rho for o in train]) - z[0]) / z[1]
    zh = (np.array([o.H for o in train]) - z[2]) / z[3]
    best = None
    for c0 in C0_GRID:
        s = B / (B + c0)
        X = np.column_stack([np.ones_like(s), xn, s, s * zr, s * zh])
        beta, *_ = np.linalg.lstsq(X, u, rcond=None)
        err = float(((X @ beta - u) ** 2).mean())
        if best is None or err < best[0]:
            best = (err, float(c0), beta)
    return FastLaw(best[2], best[1], ref, z)


def make_obs(data, cells, scales, ks):
    """cells: {(scale, env): curve of length 16}; observations at checkpoint indices ks."""
    out = []
    for (s, e), cur in cells.items():
        if s in scales:
            p = data.probes[s, e]
            out += [Observation(data.params[s], e, float(BUDGET[k]), float(cur[k]), p['rho'], p['H']) for k in ks]
    return out


def law_predict(model, data, scale, env, k):
    p = data.probes[scale, env]
    return model.predict(data.params[scale], float(BUDGET[k]), p['rho'], p['H'])


# ------------------------------------------------------------------------------------------------- P1

def b_curve(U, gm, scale, env):
    """B's estimate at the 16 budgets: final evaluations of runs of length 100/200/400, 2-parameter fit elsewhere."""
    pts = []
    for h in (100, 200, 400):
        idx = gm[('B', scale, env, 'constant', h)]
        pts.append((h, U[idx, CIDX[h]].mean()))
    C = np.array([h * TOK for h, _ in pts], float)
    u = np.array([v for _, v in pts])
    a, c0, _ = saturating_fit(C, u)
    cur = a * BUDGET / (BUDGET + c0)
    for h, v in pts:
        cur[CIDX[h]] = v
    return cur


def p1_scales(data):
    """Scales whose pool (12 seeds), A (3), B (4+2+1) cells are complete on all four pool environments."""
    ok = []
    for s in n6.BASE_SCALES:
        need = [(('pool', s, e, 'constant', 400), 12) for e in POOL_ENVS] + [(('A', s, e, 'constant', 400), 3) for e in POOL_ENVS]
        need += [(('B', s, e, 'constant', h), n) for e in POOL_ENVS for h, n in ((100, 4), (200, 2), (400, 1))]
        if all(data.has(k, n) for k, n in need):
            ok.append(s)
    return ok


def p1_stat(data, U, gm, scales):
    truth, A, B = {}, {}, {}
    for s in scales:
        for e in POOL_ENVS:
            truth[s, e] = U[gm[('pool', s, e, 'constant', 400)]].mean(0)
            A[s, e] = U[gm[('A', s, e, 'constant', 400)]].mean(0)
            B[s, e] = b_curve(U, gm, s, e)
    out = {}
    for name, est in (('A', A), ('B', B)):
        out[f'curve_rmse_{name}'] = float(np.sqrt(np.mean([(est[c] - truth[c]) ** 2 for c in truth])))
    # (ii) Eq. 7 forecast at n3 from n1, n2 on the same four environments
    for name, est in (('A', A), ('B', B)) if all(x in scales for x in n6.BASE_SCALES) else ():
        obs = make_obs(data, est, ('n1', 'n2'), range(16))
        model = fit_law(obs, data.ref)
        pred = {e: np.array([law_predict(model, data, 'n3', e, k) for k in range(16)]) for e in POOL_ENVS}
        out[f'forecast_rmse_{name}'] = float(np.sqrt(np.mean([(pred[e] - truth['n3', e]) ** 2 for e in POOL_ENVS])))
    return out


def seed_sd(data, U, gm, scales):
    return float(np.mean([U[gm[('pool', s, e, 'constant', 400)]].std(0, ddof=1) for s in scales for e in POOL_ENVS]))


def p1(data, draws, rng):
    U = data.U()
    gm = identity_map(data)
    scales = p1_scales(data)
    if not scales:
        return {'status': 'no complete scale yet'}
    pt = p1_stat(data, U, gm, scales)
    delta = {'curve': seed_sd(data, U, gm, scales)}
    if 'forecast_rmse_A' in pt:
        delta['forecast'] = seed_sd(data, U, gm, ('n3',))
    boots = []
    for _ in range(draws):
        w = rng.multinomial(n6.TARGET_N, np.full(n6.TARGET_N, 1 / n6.TARGET_N)) / n6.TARGET_N
        boots.append(p1_stat(data, data.U(w), boot_map(data, rng), scales))
    ci = lambda f: [float(np.quantile([f(b) for b in boots], q)) for q in (.025, .975)]
    res = {'scales_scored': scales, 'point': pt, 'delta_one_seed_sd': delta}
    for q, d in [(q, delta[q]) for q in ('curve', 'forecast') if q in delta]:
        res[f'{q}_A_minus_B_ci95'] = ci(lambda b: b[f'{q}_rmse_A'] - b[f'{q}_rmse_B'])
        res[f'{q}_rmse_A_ci95'] = ci(lambda b: b[f'{q}_rmse_A'])
        res[f'{q}_rmse_B_ci95'] = ci(lambda b: b[f'{q}_rmse_B'])
        res[f'{q}_holds'] = bool(pt[f'{q}_rmse_A'] <= pt[f'{q}_rmse_B'] + d)
    res['P1_holds'] = bool(res['curve_holds'] and res.get('forecast_holds', False)) if 'forecast_holds' in res else None
    res['P1_note'] = 'complete only when n1, n2, n3 are all scored' if 'forecast_holds' not in res else ''
    res['draws'] = draws
    return res


# ------------------------------------------------------------------------------------------------- P2

def a_cells(data, U, gm, scales):
    return {(s, e): U[gm[('A', s, e, 'constant', 400)]].mean(0) for s in scales for e in data.envs if ('A', s, e, 'constant', 400) in gm}


def p2_stat(data, U, gm, with_n4, curves=False):
    train = n6.BASE_SCALES
    cells = a_cells(data, U, gm, n6.ALL_SCALES if with_n4 else train)
    out = {}
    laws = {}
    for name, ks in (('prefix50', range(8)), ('prefix25', range(4)), ('full', range(16))):
        laws[name] = fit_law(make_obs(data, cells, train, ks), data.ref)
    for name, m in laws.items():
        errs = np.array([law_predict(m, data, s, e, 15) - cells[s, e][15] for s in train for e in data.envs])
        out[f'law_{name}_rmse_cmax'] = float(np.sqrt((errs ** 2).mean()))
    out['law_ratio_prefix50_over_full'] = out['law_prefix50_rmse_cmax'] / out['law_full_rmse_cmax']
    out['law_ratio_prefix25_over_full'] = out['law_prefix25_rmse_cmax'] / out['law_full_rmse_cmax']
    # rank accuracy at C_max on a held-out scale: n4 if run (fits on n1..n3), else n3 with fits on n1..n2
    def rank(model, scale):
        obs = [Observation(data.params[scale], e, float(C_MAX), float(cells[scale, e][15]), data.probes[scale, e]['rho'], data.probes[scale, e]['H']) for e in data.envs]
        return pairwise_rank_accuracy(obs, [model.predict_obs(o) for o in obs])
    variants = [('n3_fit_n1n2', ('n1', 'n2'), 'n3')] + ([('n4_fit_n1n3', train, 'n4')] if with_n4 else [])
    for tag, tr, held in variants:
        for name, ks in (('prefix50', range(8)), ('full', range(16))):
            m = fit_law(make_obs(data, cells, tr, ks), data.ref)
            out[f'rank_acc_{tag}_{name}'] = rank(m, held)
        out[f'rank_acc_{tag}_gap'] = out[f'rank_acc_{tag}_prefix50'] - out[f'rank_acc_{tag}_full']
    return out, cells


def per_cell_curve_arms(data, cells, scales):
    """Per-cell sigmoid and saturating-form prefix versus full fits, forecast at C_max (secondary arms; point estimates)."""
    res = {}
    for form in ('sigmoid', 'saturating'):
        rows = []
        for (s, e), cur in cells.items():
            if s not in scales:
                continue
            r = {'scale': s, 'env': e, 'obs_cmax': float(cur[15])}
            for name, n in (('prefix50', 8), ('prefix25', 4), ('full', 16)):
                if form == 'sigmoid':
                    r[name] = float(sigmoid_predict(sigmoid_fit(BUDGET[:n], cur[:n]), C_MAX))
                else:
                    a, c0, _ = saturating_fit(BUDGET[:n], cur[:n])
                    r[name] = float(a * C_MAX / (C_MAX + c0))
            rows.append(r)
        def rm(sel, name):
            sub = [r for r in rows if sel(r)]
            return float(np.sqrt(np.mean([(r[name] - r['obs_cmax']) ** 2 for r in sub]))) if sub else None
        out = {}
        for tag, sel in [('all', lambda r: True)] + [(s, (lambda s: lambda r: r['scale'] == s)(s)) for s in scales] + [('U_cmax_below_0', lambda r: r['obs_cmax'] < 0), ('U_cmax_at_least_0', lambda r: r['obs_cmax'] >= 0)]:
            full = rm(sel, 'full')
            out[tag] = {'n_cells': sum(1 for r in rows if sel(r)), 'prefix50': rm(sel, 'prefix50'), 'prefix25': rm(sel, 'prefix25'), 'full': full,
                        'ratio50': (rm(sel, 'prefix50') / full) if full else None}
        res[form] = out
    return res


def p2(data, draws, rng):
    with_n4 = any(k[0] == 'A' and k[1] == 'n4' for k in data.groups)
    U = data.U()
    gm = identity_map(data)
    pt, cells = p2_stat(data, U, gm, with_n4)
    boots = []
    for _ in range(draws):
        w = rng.multinomial(n6.TARGET_N, np.full(n6.TARGET_N, 1 / n6.TARGET_N)) / n6.TARGET_N
        boots.append(p2_stat(data, data.U(w), boot_map_seeds_per_scale(data, rng), with_n4)[0])
    ci = lambda key: [float(np.quantile([b[key] for b in boots], q)) for q in (.025, .975)]
    res = {'point': pt, 'with_n4': with_n4, 'draws': draws,
           'ci95': {k: ci(k) for k in pt}, 'per_cell_arms_point': per_cell_curve_arms(data, cells, n6.ALL_SCALES if with_n4 else n6.BASE_SCALES)}
    tag = 'n4_fit_n1n3' if with_n4 else 'n3_fit_n1n2'
    res['criterion1_ratio_le_1.25'] = bool(pt['law_ratio_prefix50_over_full'] <= 1.25)
    res['criterion2_rank_gap_within_0.10'] = bool(abs(pt[f'rank_acc_{tag}_gap']) <= 0.10)
    res['rank_variant_used'] = tag
    res['P2_holds'] = bool(res['criterion1_ratio_le_1.25'] and res['criterion2_rank_gap_within_0.10'])
    return res


# ------------------------------------------------------------------------------------------------- P3

def p3_rows(data, U):
    """One row per (A run, increment i->i+1, i = 0..14): features of the window before checkpoint i."""
    rows = []
    for key, idx in data.groups.items():
        if key[0] != 'A' or key[1] not in n6.BASE_SCALES:
            continue
        for ri in idx:
            run = data.runs[ri]
            rho = np.array([r['rho_roll'] for r in run['rows']])
            H = np.array([r['H_roll'] for r in run['rows']])
            for i in range(15):
                rows.append({'run': int(ri), 'scale': key[1], 'env': key[2], 'i': i, 'dU': float(U[ri, i + 1] - U[ri, i]),
                             'rho': float(rho[i]), 'H': float(H[i]), 'U_prev': float(U[ri, i] - (U[ri, i - 1] if i else 0.0))})
    return rows


def design(data, rows, c0, z):
    x_n = lambda s: np.log(data.params[s] / data.ref[0]) / np.log(data.ref[1] / data.ref[0])
    s_of = lambda i: BUDGET[i] / (BUDGET[i] + c0)
    X = []
    for r in rows:
        ds = s_of(r['i'] + 1) - s_of(r['i'])
        X.append([1.0, x_n(r['scale']), ds, ds * (np.log(r['rho']) - z[0]) / z[1], ds * (r['H'] - z[2]) / z[3]])
    return np.array(X)


def fit_rolling(data, rows):
    cell = defaultdict(list)
    for r in rows:
        cell[r['scale'], r['env'], r['i']].append((np.log(r['rho']), r['H']))
    lr = np.array([np.mean([a for a, _ in v]) for v in cell.values()])
    hh = np.array([np.mean([b for _, b in v]) for v in cell.values()])
    z = (lr.mean(), lr.std() or 1.0, hh.mean(), hh.std() or 1.0)
    y = np.array([r['dU'] for r in rows])
    best = None
    for c0 in C0_GRID:
        X = design(data, rows, c0, z)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        sse = float(((X @ beta - y) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, c0, beta)
    return {'c0': best[1], 'beta': best[2], 'z': z}


def predict_rolling(data, m, rows):
    return design(data, rows, m['c0'], m['z']) @ m['beta']


def start_only_increments(data, U, cell_runs, rows):
    """Eq. 7 on cell-mean curves with start-policy rho, H; implied increments Uhat(C_{i+1}) - Uhat(C_i) for `rows`."""
    cells = {k: U[v].mean(0) for k, v in cell_runs.items()}
    obs = make_obs(data, cells, n6.BASE_SCALES, range(16))
    m = fit_law(obs, data.ref)
    cache = {}
    out = []
    for r in rows:
        key = (r['scale'], r['env'])
        if key not in cache:
            cache[key] = np.array([law_predict(m, data, r['scale'], r['env'], k) for k in range(16)])
        out.append(cache[key][r['i'] + 1] - cache[key][r['i']])
    return np.array(out)


def p3(data, draws, rng):
    U = data.U()
    rows = [r for r in p3_rows(data, U) if r['rho'] > 0 and r['i'] >= 1]
    n_all = len([r for r in p3_rows(data, U) if r['i'] >= 1])
    envs = sorted({r['env'] for r in rows})
    runs = sorted({r['run'] for r in rows})
    cell_runs_all = {(k[1], k[2]): v for k, v in data.groups.items() if k[0] == 'A' and k[1] in n6.BASE_SCALES}
    results = {}
    for cv in ('loeo', 'loto'):
        err = {m: {} for m in ('rolling', 'zero', 'previous', 'start_only')}
        folds = envs if cv == 'loeo' else runs
        for f in folds:
            test = [r for r in rows if (r['env'] == f if cv == 'loeo' else r['run'] == f)]
            train = [r for r in rows if not (r['env'] == f if cv == 'loeo' else r['run'] == f)]
            m = fit_rolling(data, train)
            pr = predict_rolling(data, m, test)
            if cv == 'loeo':
                cr = {k: v for k, v in cell_runs_all.items() if k[1] != f}
            else:
                cr = {k: np.array([x for x in v if x != f]) for k, v in cell_runs_all.items()}
            so = start_only_increments(data, U, cr, test)
            y = np.array([r['dU'] for r in test])
            prev = np.array([r['U_prev'] for r in test])
            for name, p in (('rolling', pr), ('zero', np.zeros(len(y))), ('previous', prev), ('start_only', so)):
                for rr, e in zip(test, (p - y) ** 2):
                    err[name].setdefault(rr['run'], []).append(e)
        per = {m: np.array([np.mean(d[r]) for r in runs]) for m, d in err.items()}
        r = {'n_trajectories': len(runs), 'n_increment_rows': len(rows), 'mse': {m: float(v.mean()) for m, v in per.items()}}
        for base in ('zero', 'previous', 'start_only'):
            diff = per[base] - per['rolling']
            bs = [diff[rng.integers(len(diff), size=len(diff))].mean() for _ in range(draws)]
            r[f'{base}_minus_rolling'] = {'mean': float(diff.mean()), 'ci95': [float(np.quantile(bs, .025)), float(np.quantile(bs, .975))]}
        results[cv] = r
    full = fit_rolling(data, rows)
    results['full_fit'] = {'c0_steps': float(full['c0'] / TOK), 'beta': dict(zip(['c0', 'cN', 'cC', 'c_rho', 'c_H'], map(float, full['beta'])))}
    results['rows_excluded_rho_zero'] = n_all - len(rows)
    results['P3_holds'] = bool(all(results[cv][f'{b}_minus_rolling']['ci95'][0] > 0 for cv in ('loeo', 'loto') for b in ('zero', 'previous', 'start_only')))
    results['draws'] = draws
    return results


# ------------------------------------------------------------------------------------------------- P5

def p5_scales(data):
    ok = []
    for s in ('n2', 'n3'):
        need = [(('A', s, e, 'constant', 400), 3) for e in POOL_ENVS] + [(('cosL', s, e, 'cosine', 400), 3) for e in POOL_ENVS]
        need += [(('B', s, e, 'constant', h), n) for e in POOL_ENVS for h, n in ((100, 4), (200, 2))]
        need += [(('cosS', s, e, 'cosine', h), n) for e in POOL_ENVS for h, n in ((100, 4), (200, 2))]
        if all(data.has(k, n) for k, n in need):
            ok.append(s)
    return ok


def p5_stat(data, U, gm, scales=('n2', 'n3')):
    out = {}
    for b in (100, 200):
        eff = {}
        for sched, long_key, short_key in (('constant', 'A', 'B'), ('cosine', 'cosL', 'cosS')):
            vals = []
            for s in scales:
                for e in POOL_ENVS:
                    long_ = U[gm[(long_key, s, e, sched, 400)], CIDX[b]].mean()
                    fresh = U[gm[(short_key, s, e, sched, b)], CIDX[b]].mean()
                    vals.append(long_ - fresh)
            eff[sched] = float(np.mean(vals))
        out[f'effect_constant_{b}'], out[f'effect_cosine_{b}'] = eff['constant'], eff['cosine']
        out[f'diff_{b}'] = eff['cosine'] - eff['constant']
    return out


def p5(data, draws, rng):
    U = data.U()
    scales = p5_scales(data)
    if not scales:
        return {'status': 'no complete scale yet'}
    pt = p5_stat(data, U, identity_map(data), scales)
    boots = []
    for _ in range(draws):
        w = rng.multinomial(n6.TARGET_N, np.full(n6.TARGET_N, 1 / n6.TARGET_N)) / n6.TARGET_N
        boots.append(p5_stat(data, data.U(w), boot_map(data, rng), scales))
    ci = {k: [float(np.quantile([b[k] for b in boots], q)) for q in (.025, .975)] for k in pt}
    sig = {b: (ci[f'diff_{b}'][0] > 0 or ci[f'diff_{b}'][1] < 0) for b in (100, 200)}
    same_sign = np.sign(pt['diff_100']) == np.sign(pt['diff_200'])
    return {'scales_scored': scales, 'point': pt, 'ci95': ci, 'significant_at': {str(k): bool(v) for k, v in sig.items()},
            'P5_holds': bool(all(sig.values()) and same_sign), 'direction': 'cosine effect more negative than constant' if pt['diff_100'] < 0 else 'cosine effect more positive than constant', 'draws': draws}


# ------------------------------------------------------------------------------------------------- variance decomposition

def variance_decomposition(data):
    U = data.U()
    out = {}
    for s in n6.ALL_SCALES:
        within, seedvar, cmax_sd = [], [], []
        for e in POOL_ENVS:
            key = ('pool', s, e, 'constant', 400)
            if key not in data.groups:
                continue
            fits, res = [], []
            for ri in data.groups[key]:
                a, c0, sse = saturating_fit(BUDGET, U[ri])
                fits.append(a * BUDGET / (BUDGET + c0))
                res.append(sse / (16 - 2))
            within.append(np.mean(res))
            seedvar.append(np.var(np.array(fits), axis=0, ddof=1).mean())
            cmax_sd.append(U[data.groups[key], 15].std(ddof=1))
        if within:
            out[s] = {'within_run_var': float(np.mean(within)), 'seed_var_of_fitted_curves': float(np.mean(seedvar)),
                      'ratio_within_over_seed': float(np.mean(within) / np.mean(seedvar)), 'seed_sd_at_cmax': float(np.mean(cmax_sd)),
                      'n_cells': len(within)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, default=n6.RESULTS)
    ap.add_argument('--out', type=Path, default=n6.HERE / 'analysis.json')
    ap.add_argument('--draws', type=int, default=2000)
    ap.add_argument('--only', default='p1,p2,p3,p5,var')
    a = ap.parse_args()
    data = Data(a.results)
    rng = np.random.default_rng(2506)
    todo = set(a.only.split(','))
    res = {'n_runs': len(data.runs), 'runs_by_stage': {k: sum(r['stage'] == k for r in data.runs) for k in sorted({r['stage'] for r in data.runs})}}
    if 'p1' in todo: res['P1'] = p1(data, a.draws, rng)
    complete_main = all(data.has(('A', sc, e, 'constant', 400), 3) for sc in n6.BASE_SCALES for e in data.envs)
    if 'p2' in todo: res['P2'] = p2(data, a.draws, rng) if complete_main else {'status': 'main matrix n1-n3 incomplete'}
    if 'p3' in todo: res['P3'] = p3(data, a.draws, rng) if complete_main else {'status': 'main matrix n1-n3 incomplete'}
    if 'p5' in todo: res['P5'] = p5(data, a.draws, rng)
    if 'var' in todo: res['variance_decomposition'] = variance_decomposition(data)
    n6.write(a.out, res)
    print(json.dumps(res, indent=1)[:6000])


if __name__ == '__main__':
    main()
