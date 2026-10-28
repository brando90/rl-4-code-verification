"""TLDR: P6 (Q1) from the three Delphi replica measurement files per scale: measurable-environment counts, seed SD versus between-environment SD of log rho and H, pairwise Spearman of the environment ranking (CPU)."""
import itertools
import json
import sys
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parent / 'results'
TAGS = {'3.4B': ['q1_3p4b_base', 'q1_3p4b_s42', 'q1_3p4b_s62746'], '9.7B': ['q1_9p7b_base', 'q1_9p7b_s42', 'q1_9p7b_s62746']}


def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def stats(reps, envs):
    out = {}
    for name, f in (('log_rho', lambda v: np.log(max(v['rho'], 1e-9))), ('H', lambda v: v['H'])):
        m = np.array([[f(r[e]) for e in envs] for r in reps])  # replicas x envs
        seed_sd = float(np.sqrt(np.mean(np.var(m, axis=0, ddof=1))))
        between = float(np.std(m.mean(axis=0), ddof=1))
        rho = [spearman(m[i], m[j]) for i, j in itertools.combinations(range(len(reps)), 2)]
        out[name] = {'seed_sd_pooled': seed_sd, 'between_env_sd': between, 'ratio': seed_sd / between if between > 0 else None,
                     'ratio_le_0.25': bool(between > 0 and seed_sd / between <= 0.25), 'spearman_pairs': rho, 'spearman_min': min(rho)}
    return out


res = {}
for scale, tags in TAGS.items():
    reps = [json.loads((R / f'{t}_measure.json').read_text())['envs'] for t in tags]
    allenvs = list(reps[0])
    common = [e for e in allenvs if all(r[e]['q_mixed_empirical'] >= 0.2 for r in reps)]
    res[scale] = {'measurable_per_replica': {t: [e for e in allenvs if reps[i][e]['q_mixed_empirical'] >= 0.2] for i, t in enumerate(tags)},
                  'n_measurable_per_replica': [sum(r[e]['q_mixed_empirical'] >= 0.2 for e in allenvs) for r in reps],
                  'measurable_in_all_replicas': common, 'P6_precondition_ge4_met': len(common) >= 4,
                  'descriptive_common_measurable': stats(reps, common) if len(common) >= 3 else None,
                  'descriptive_7_environments_NOT_PROTOCOL': stats(reps, [e for e in allenvs if e != 'rg/simple_equations/L1'])}
Path(R / 'p6_q1.json').write_text(json.dumps(res, indent=1))
for s, v in res.items():
    print(s, 'n measurable per replica', v['n_measurable_per_replica'], 'in all', v['measurable_in_all_replicas'], 'precond', v['P6_precondition_ge4_met'])
    for k in ('descriptive_common_measurable', 'descriptive_7_environments_NOT_PROTOCOL'):
        d = v[k]
        if d:
            print(' ', k, {m: (round(x['seed_sd_pooled'], 3), round(x['between_env_sd'], 3), round(x['ratio'], 2), round(x['spearman_min'], 2)) for m, x in d.items()})
