"""TLDR: Stage 0 CPU analyses of experiment 25 (checkpoint reuse for the rho-H law): 0b prefix extrapolation and Night 4 to 5 retrospective check on the toy, 0c SFT rungs versus fresh runs on the 08 data, written to results/*.json."""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from pathlib import Path

import numpy as np

from rl4cv.experience import Response, groups_from_records, measure_environment
from rl4cv.utility_model import Observation, RHO_H, fit_utility_model, pairwise_rank_accuracy

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[0]
REPO = HERE.parents[2]
TOY = REPO / 'experiments/16_toy_env_generation_ginc_hmm_rho_h_law'
NIGHTS = {'night4': TOY / 'expt_v4/results/night4', 'night5': TOY / 'expt_v5/results/night5'}
EIGHT = next((REPO / 'experiments').glob('08_qwen3_base_matched_lean_sft_*'))
LADDER = EIGHT / 'expt_v1/results/ladder'
V27 = EIGHT / 'expt_v27_data_size_seeds/results/analysis'
SCALES = ['n1', 'n2', 'n3', 'n4']
STEPS = (25, 50, 100)
TOKENS_PER_STEP = 16 * 8 * 4  # BATCH * GROUP * K (night4.py)
SEEDS = (0, 1, 2)
MULTISETS = list(itertools.combinations_with_replacement(SEEDS, 3))  # the 10 distinct seed resamples
C0_GRID = [TOKENS_PER_STEP * math.exp(x) for x in np.linspace(math.log(10), math.log(4000), 41)]
BOOT_DRAWS, BOOT_SEED = 10_000, 20261028


# ---------------------------------------------------------------- toy (0b)

def load_night(path: Path):
    params = {s: json.loads((path / f'{s}_meta.json').read_text())['n_params'] for s in SCALES}
    probes = {(s, r['env']): (r['rho'], r['H']) for s in SCALES for r in json.loads((path / f'{s}_probe.json').read_text())}
    cells = json.loads((path / 'cells.json').read_text())
    return params, probes, cells


def seed_mean_obs(cells, params, probes, scales, steps, weights=None):
    """Observation per (scale, env, budget) = weighted mean utility over seeds (weights: seed -> multiplicity)."""
    weights = weights or {s: 1 for s in SEEDS}
    acc: dict = {}
    for r in cells:
        if r['scale'] in scales and r['tokens'] // TOKENS_PER_STEP in steps:
            acc.setdefault((r['scale'], r['env'], r['tokens']), {})[r['seed']] = r['utility']
    out = []
    for (s, e, b), by_seed in sorted(acc.items()):
        w = {k: weights.get(k, 0) for k in by_seed}
        u = sum(w[k] * by_seed[k] for k in by_seed) / sum(w.values())
        out.append(Observation(params[s], e, float(b), float(u), probes[s, e][0], probes[s, e][1]))
    return out


def fit_c0(obs, ref, grid=True):
    """Eq. 7 fit; C0 by the 41-point grid minimizing training RMSE, or the fixed training-median default."""
    if not grid or len({o.budget for o in obs}) < 2:
        return fit_utility_model(obs, RHO_H, ref_scales=ref)
    best, best_rmse = None, math.inf
    y = np.array([o.utility for o in obs])
    for c in C0_GRID:
        m = fit_utility_model(obs, RHO_H, C0=c, ref_scales=ref)
        rmse = float(np.sqrt(np.mean((np.array([m.predict_obs(o) for o in obs]) - y) ** 2)))
        if rmse < best_rmse:
            best, best_rmse = m, rmse
    return best


def score(model, target_obs):
    y0 = np.array([o.utility for o in target_obs])
    preds = [model.predict_obs(o) for o in target_obs]
    y = np.array([o.utility for o in target_obs])
    err = np.array(preds) - y
    neg = y < 0
    return {'rmse_pp': float(100 * np.sqrt(np.mean(err ** 2))),
            'rmse_pp_U_lt_0': float(100 * np.sqrt(np.mean(err[neg] ** 2))) if neg.any() else None,
            'rmse_pp_U_ge_0': float(100 * np.sqrt(np.mean(err[~neg] ** 2))) if (~neg).any() else None,
            'rmse_pp_predict_zero': float(100 * np.sqrt(np.mean(y0 ** 2))), 'sd_pp_of_observed_U': float(100 * y0.std()),
            'rank_acc': pairwise_rank_accuracy(target_obs, preds), 'n_cells': len(target_obs), 'n_U_lt_0': int(neg.sum())}


PREFIX_FITS = {'FULL': STEPS, 'PREFIX50': (25, 50), 'PREFIX25': (25,)}


def prefix_block(cells, params, probes, weights=None):
    """P2 scores: held-out n4 (fit n1..n3) and n3 (fit n1..n2), plus in-scale step-100 forecast from each prefix."""
    ref = (params['n1'], params['n3'])
    out = {}
    for tag, train_scales, target in (('n4_holdout', ('n1', 'n2', 'n3'), 'n4'), ('n3_holdout', ('n1', 'n2'), 'n3')):
        tgt = seed_mean_obs(cells, params, probes, (target,), (100,), weights)
        for name, steps in PREFIX_FITS.items():
            train = seed_mean_obs(cells, params, probes, train_scales, steps, weights)
            for c0name, grid in (('gridC0', True), ('medianC0', False)):
                if name == 'PREFIX25' and grid:
                    continue  # one budget: C0 not identifiable, only the fixed default exists
                out[f'{tag}/{name}/{c0name}'] = score(fit_c0(train, ref, grid), tgt)
    for s in ('n1', 'n2', 'n3'):
        tgt = seed_mean_obs(cells, params, probes, (s,), (100,), weights)
        for name, steps in PREFIX_FITS.items():
            train = seed_mean_obs(cells, params, probes, ('n1', 'n2', 'n3'), steps, weights)
            out[f'inscale_{s}/{name}/gridC0' if name != 'PREFIX25' else f'inscale_{s}/{name}/medianC0'] = score(fit_c0(train, ref, name != 'PREFIX25'), tgt)
    return out


def p2_verdict(block, tag):
    f, p = block[f'{tag}/FULL/gridC0'], block[f'{tag}/PREFIX50/gridC0']
    ratio = p['rmse_pp'] / f['rmse_pp']
    gap = f['rank_acc'] - p['rank_acc']
    return {'rmse_ratio': ratio, 'rank_acc_gap_full_minus_prefix': gap, 'holds': bool(ratio <= 1.25 and gap <= 0.10)}


def run_prefix(night):
    params, probes, cells = load_night(NIGHTS[night])
    point = prefix_block(cells, params, probes)
    ranges = {}
    per_multiset = []
    for ms in MULTISETS:
        w = {s: ms.count(s) for s in SEEDS}
        b = prefix_block(cells, params, probes, w)
        per_multiset.append({'multiset': list(ms), 'p2_n4': p2_verdict(b, 'n4_holdout'), 'p2_n3': p2_verdict(b, 'n3_holdout'),
                             'block': b})
    for key in point:
        for metric in ('rmse_pp', 'rank_acc'):
            vals = [m['block'][key][metric] for m in per_multiset]
            ranges[f'{key}/{metric}'] = [min(vals), max(vals)]
    return {'point': point, 'p2_primary_n4': p2_verdict(point, 'n4_holdout'), 'p2_secondary_n3': p2_verdict(point, 'n3_holdout'),
            'seed_multiset_ranges': ranges,
            'p2_by_multiset': [{k: m[k] for k in ('multiset', 'p2_n4', 'p2_n3')} for m in per_multiset],
            'n_cells_per_target': 16, 'n_trajectories_per_scale_env': 3}


def cross_start():
    """Fit FULL on Night 4 (n1..n3) and score on Night 5 (all four scales, steps 25/50/100). RETROSPECTIVE."""
    p4, pr4, c4 = load_night(NIGHTS['night4'])
    p5, pr5, c5 = load_night(NIGHTS['night5'])
    out = {}
    for ms in [None] + MULTISETS:
        w = None if ms is None else {s: ms.count(s) for s in SEEDS}
        ref = (p4['n1'], p4['n3'])
        model = fit_c0(seed_mean_obs(c4, p4, pr4, ('n1', 'n2', 'n3'), STEPS, w), ref, True)
        n4 = {(o.scale, o.env, o.budget): o.utility for o in seed_mean_obs(c4, p4, pr4, SCALES, STEPS, w)}  # keyed by n_params
        res = {}
        for s in SCALES:
            for st in STEPS:
                tgt = [o for o in seed_mean_obs(c5, p5, pr5, (s,), (st,), w)]
                preds = [model.predict_obs(o) for o in tgt]
                y = np.array([o.utility for o in tgt])
                # observations carry Night 5 probes; map to env names for the baselines
                persist = np.array([n4[(p4[s], e, o.budget)] for o, e in zip(tgt, [t.env for t in tgt])])
                mean4 = np.mean([v for (ss, e, b), v in n4.items() if ss == p4[s] and b == tgt[0].budget])
                res[f'{s}/step{st}'] = {
                    'law': {'rmse_pp': float(100 * np.sqrt(np.mean((np.array(preds) - y) ** 2))), 'rank_acc': pairwise_rank_accuracy(tgt, preds)},
                    'persistence': {'rmse_pp': float(100 * np.sqrt(np.mean((persist - y) ** 2))), 'rank_acc': pairwise_rank_accuracy(tgt, list(persist))},
                    'night4_env_mean': {'rmse_pp': float(100 * np.sqrt(np.mean((mean4 - y) ** 2)))},
                    'n_cells': len(tgt)}
        out['point' if ms is None else str(ms)] = res
    point = out.pop('point')
    keys = list(point)
    ranges = {}
    for k in keys:
        for arm in ('law', 'persistence', 'night4_env_mean'):
            vals = [o[k][arm]['rmse_pp'] for o in out.values()]
            ranges[f'{k}/{arm}/rmse_pp'] = [min(vals), max(vals)]
    return {'point': point, 'seed_multiset_ranges': ranges, 'label': 'RETROSPECTIVE: Night 5 outcomes were committed before this fit; not a forecast'}


# ---------------------------------------------------------------- real data (0c)

def read_cells(path: Path, reward_key: str):
    rows = list(csv.DictReader(open(path)))
    rows.sort(key=lambda r: (r['task_id'], int(r['sample_idx'])))
    recs = [{'task_id': r['task_id'], 'reward': float(r[reward_key]), 'generated_tokens': int(r['generated_tokens']),
             'admitted': r['capped'] not in ('True', 'true', '1')} for r in rows]
    return recs, sum(r.get('unparseable', 'False') != 'False' for r in rows)


def task_arrays(recs):
    """Per-task sufficient statistics for the bootstrap: admitted mass a, token total T, raw mass, mixed flag, admitted count."""
    groups = groups_from_records(recs, reward_key='reward')
    from rl4cv.experience import group_masses, is_mixed
    a, raw, T, mix, adm, n, rew = [], [], [], [], [], [], []
    for g in groups:
        r, am, _ = group_masses(g)
        raw.append(r); a.append(am); T.append(sum(x.generated_tokens for x in g)); mix.append(float(is_mixed(g)))
        adm.append(sum(x.admitted for x in g)); n.append(len(g)); rew.append(sum(x.reward for x in g))
    return {k: np.array(v, dtype=float) for k, v in dict(a=a, raw=raw, T=T, mixed=mix, adm=adm, n=n, rew=rew).items()}, groups


def metrics_from_weights(t, W):
    """rho, H, q_mixed, admission rate, mean tokens, mean reward for each weight row of W (task counts); vectorized."""
    Sa, Sa2 = W @ t['a'], W @ (t['a'] ** 2)
    ST, Sn, Sadm = W @ t['T'], W @ t['n'], W @ t['adm']
    ngroups = W.sum(1)
    with np.errstate(divide='ignore', invalid='ignore'):
        rho = 1e6 * Sa / ST
        H = np.where(Sa > 0, Sa ** 2 / (ngroups * Sa2), 0.0)
    return {'rho': rho, 'H': H, 'q_mixed': (W @ t['mixed']) / ngroups, 'admission': Sadm / Sn, 'mean_tokens': ST / Sn,
            'mean_reward': (W @ t['rew']) / Sn}


def point_metrics(recs):
    m = measure_environment(groups_from_records(recs, reward_key='reward'))
    return m


def boot_weights(n_tasks, draws=BOOT_DRAWS, seed=BOOT_SEED):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_tasks, size=(draws, n_tasks))
    W = np.zeros((draws, n_tasks))
    for i in range(draws):
        W[i] = np.bincount(idx[i], minlength=n_tasks)
    return W


def ci(x):
    x = x[np.isfinite(x)]
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5)), int(len(x))]


def run_real():
    files = {}
    for p in sorted(LADDER.glob('*_validation_cells.csv')):
        files[f'ladder/{p.stem[:-6]}'] = (p, 'kernel_binary')
    for p in sorted(V27.glob('v27_f*_cells.csv')) + sorted(V27.glob('v16_v4_*_cells.csv')):
        files[f'fresh/{p.stem[:-6]}'] = (p, 'binary_success')
    data, W, unparse = {}, None, {}
    for name, (p, rk) in files.items():
        recs, n_unp = read_cells(p, rk)
        unparse[name] = n_unp
        t, groups = task_arrays(recs)
        tasks = sorted({r['task_id'] for r in recs})
        if len(t['a']) != 135 or set(t['n']) != {8.0}:
            raise ValueError(f'{name}: expected 135 tasks x 8 samples, got {len(t["a"])} x {set(t["n"])}')
        # tasks must align across cells for the paired bootstrap: reorder by sorted task id
        data[name] = (recs, t)
    W = boot_weights(135)
    table = {}
    for name, (recs, t) in data.items():
        pm = point_metrics(recs)
        bm = metrics_from_weights(t, W)
        table[name] = {'point': {'rho': pm.rho, 'H': pm.H, 'q_mixed': pm.q_mixed_empirical, 'n_mixed': round(pm.q_mixed_empirical * pm.n_groups),
                                 'admission': pm.admission_rate, 'mean_tokens': pm.mean_generated_tokens, 'mean_reward': pm.mean_reward},
                       'ci': {k: ci(v) for k, v in bm.items()}}
        vec = metrics_from_weights(t, np.ones((1, W.shape[1])))
        assert abs(vec['rho'][0] - pm.rho) < 1e-6 * max(1, pm.rho) and abs(vec['H'][0] - pm.H) < 1e-9, name
    return data, W, table, unparse


def task_order_check(data):
    ids = {}
    for name, (recs, t) in data.items():
        ids[name] = [r['task_id'] for r in recs][::8]
    first = next(iter(ids.values()))
    return all(v == first for v in ids.values()), {k: len(set(v)) for k, v in ids.items()}


def p4(data, W, rung_names, fresh_names, margin_h=0.073, margin_lr=0.49):
    """Pooled (mean over fractions) paired task-bootstrap difference rung minus mean of the fresh seeds."""
    res = {}
    mets = {}
    for f, (rung, fresh) in {'50': (rung_names['50'], fresh_names['50']), '100': (rung_names['100'], fresh_names['100'])}.items():
        r = metrics_from_weights(data[rung][1], W)
        fr = [metrics_from_weights(data[n][1], W) for n in fresh]
        pt_r = metrics_from_weights(data[rung][1], np.ones((1, W.shape[1])))
        pt_f = [metrics_from_weights(data[n][1], np.ones((1, W.shape[1]))) for n in fresh]
        mets[f] = {'dlogrho': np.log(r['rho']) - np.mean([np.log(x['rho']) for x in fr], 0),
                   'dH': r['H'] - np.mean([x['H'] for x in fr], 0),
                   'pt_dlogrho': float(np.log(pt_r['rho'][0]) - np.mean([np.log(x['rho'][0]) for x in pt_f])),
                   'pt_dH': float(pt_r['H'][0] - np.mean([x['H'][0] for x in pt_f]))}
    for key, margin, pk in (('dlogrho', margin_lr, 'pt_dlogrho'), ('dH', margin_h, 'pt_dH')):
        pooled = (mets['50'][key] + mets['100'][key]) / 2
        lo, hi, n = ci(pooled)
        pooled_pt = (mets['50'][pk] + mets['100'][pk]) / 2
        per = {f: {'point': mets[f][pk], 'ci': ci(mets[f][key])} for f in ('50', '100')}
        verdict = 'EQUIVALENT' if (-margin <= lo and hi <= margin) else ('NOT EQUIVALENT' if (hi < -margin or lo > margin) else 'INCONCLUSIVE')
        res[key] = {'pooled_point': pooled_pt, 'pooled_ci95': [lo, hi], 'n_valid_draws': n, 'half_width': (hi - lo) / 2, 'margin': margin,
                    'verdict': verdict, 'per_fraction': per}
        if key == 'dlogrho':
            res[key]['fine_margin_0.244'] = 'inside' if (-0.244 <= lo and hi <= 0.244) else 'not inside'
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('stage', choices=['prefix', 'cross', 'real', 'all'])
    a = ap.parse_args()
    out = HERE / 'results'
    out.mkdir(exist_ok=True)
    if a.stage in ('prefix', 'all'):
        for n in NIGHTS:
            (out / f'0b_prefix_{n}.json').write_text(json.dumps(run_prefix(n), indent=1))
    if a.stage in ('cross', 'all'):
        (out / '0b_cross_start_night4_to_night5.json').write_text(json.dumps(cross_start(), indent=1))
    if a.stage in ('real', 'all'):
        data, W, table, unparse = run_real()
        for n in ('ladder/sft_1p7B_f0p5_validation', 'ladder/sft_1p7B_f1p0_validation'):
            assert unparse[n] == 0, f'{n} has unparseable rows'
        same, nuniq = task_order_check(data)
        rung = {'50': 'ladder/sft_1p7B_f0p5_validation', '100': 'ladder/sft_1p7B_f1p0_validation'}
        fresh = {'50': ['fresh/v27_f0p5_s20260830', 'fresh/v27_f0p5_s20260831'], '100': ['fresh/v16_v4_20260830', 'fresh/v16_v4_20260831']}
        res = {'unparseable_rows_per_file': unparse, 'table': table, 'task_order_identical_across_files': same, 'unique_tasks': nuniq, 'p4': p4(data, W, rung, fresh), 'rung': rung, 'fresh': fresh}
        (out / '0c_real_rho_h.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
