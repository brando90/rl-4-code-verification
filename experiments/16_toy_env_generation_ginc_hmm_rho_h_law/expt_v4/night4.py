"""Night 4: does a target-alignment term alpha added to the rho-H law (Eq. 7) fix environment choice on GINC?

Stages (all CPU, resumable, one PyTorch thread each). Starting policies, candidates and probes reuse expt_v2 unchanged.
  pilot   one n3 GRPO trajectory at a candidate RL strength and a pilot seed (100/101); excluded from the analysis
  choose  freeze the RL strength by the variance rule in PROTOCOL.md (reads only pilot cells and Night 2's n3 cells)
  alpha   target-alignment probe per (scale, env): gradient cosine and k-step target-dev NLL drop
  rl      one main GRPO trajectory (scale, env, seed 0/1/2) at the frozen strength
  freeze  fit law, law+alpha and baselines on n1-n3 and freeze the n4 choices before any n4 trajectory exists
  report  n4 regrets with bootstrap intervals and the frozen decision rule
"""
import argparse
from copy import deepcopy
import json
import time
from importlib import import_module
from pathlib import Path
import numpy as np
import torch
from rl4cv.forecast import freeze_forecast, verify_forecast
from rl4cv.utility_model import Observation, fit_utility_model, RHO_H

V2 = 'experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2'
g = import_module(f'{V2}.ginc')
pol = import_module(f'{V2}.policy')
r2 = import_module(f'{V2}.run')
K, TARGET, make_prompts, rewards = g.K, g.TARGET, g.make_prompts, g.rewards
SCALES, generate, grpo, rollout_loss, with_bos = pol.SCALES, pol.generate, pol.grpo, pol.rollout_loss, pol.with_bos
read, write, sha, specs, load_model, evaluate = r2.read, r2.write, r2.sha, r2.specs, r2.load_model, r2.evaluate

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/night4'
NIGHT2 = HERE.parent / 'expt_v2/results/pilot_v3'
STEPS = [25, 50, 100]
BATCH, GROUP = 16, 8
BUDGETS = [s * BATCH * GROUP * K for s in STEPS]
TARGET_N, POOL_N, HELD_N = 4000, 20000, 512
SEEDS = (0, 1, 2)
PILOT_SEEDS = (100, 101)
# Frozen candidate RL strengths, weakest first. S1 is Night 2's exact setting; its pilot statistic comes from Night 2's
# committed n3 cells (seeds 0/1), so only S2 and S3 are piloted.
SETTINGS = {'S1': {'lr': 1e-4, 'kl_coef': 1.0}, 'S2': {'lr': 3e-4, 'kl_coef': 0.1}, 'S3': {'lr': 1e-3, 'kl_coef': 0.1}}
# Alpha probe constants.
DEV_N, DEV_SEED = 512, 98          # target-dev prompts; the evaluation cohort is 4,000 prompts at seed 99
GRAD_N, GRAD_PROMPT_SEED, GRAD_SAMPLE_SEED = 256, 14, 15
PROBE_K, PROBE_SEEDS = 10, (21, 22)


def target_nll(model, prompts):
    """Teacher-forced mean per-token negative log-likelihood of the oracle four-token continuation."""
    seq = torch.cat([with_bos(prompts.x), torch.as_tensor(prompts.y)], 1)
    length = prompts.x.shape[1]
    logits = model(seq[:, :-1])[:, length:length + K]
    return -logits.log_softmax(-1).gather(-1, torch.as_tensor(prompts.y)[:, :, None]).mean()


def flat_grad(model, loss):
    model.zero_grad()
    loss.backward()
    return torch.cat([p.grad.flatten() for p in model.parameters()]).detach().clone()


def zscore(values):
    v = np.asarray(values, dtype=float)
    sd = v.std()
    return (v - v.mean()) / (sd if sd > 0 else 1.0)


def alpha_from_components(cos, dnll):
    """alpha = mean of within-scale z-scores of the gradient cosine and of the k-step target-dev NLL drop."""
    return 0.5 * (zscore(cos) + zscore(dnll))


def alpha_probe(model, spec, setting):
    dev = make_prompts(TARGET, DEV_N, DEV_SEED)
    g_tgt = flat_grad(model, target_nll(model, dev))
    p = make_prompts(spec, GRAD_N, GRAD_PROMPT_SEED)
    a = generate(model, p.x, GROUP, torch.Generator().manual_seed(GRAD_SAMPLE_SEED))
    reward, _ = rewards(a, p.y)
    ref = deepcopy(model).eval()
    loss, _ = rollout_loss(model, ref, p.x, a, reward, kl_coef=0.)  # exact KL has zero gradient at the start policy
    g_env = flat_grad(model, loss)
    cos = float(torch.nn.functional.cosine_similarity(g_env, g_tgt, dim=0))
    with torch.no_grad():
        nll0 = float(target_nll(model, dev))
    joint0 = evaluate(model, dev)['joint']
    pool = make_prompts(spec, POOL_N, 13)
    drops, djoint = [], []
    for seed in PROBE_SEEDS:
        m = deepcopy(model)
        ref = deepcopy(model).eval()
        for q in ref.parameters():
            q.requires_grad_(False)
        grpo(m, ref, pool, PROBE_K, [], None, seed, batch=BATCH, group=GROUP, **setting)
        with torch.no_grad():
            drops.append(nll0 - float(target_nll(m, dev)))
        djoint.append(evaluate(m, dev)['joint'] - joint0)
    return {'env': spec.name, 'grad_cos': cos, 'dev_nll_start': nll0, 'dev_nll_drop': float(np.mean(drops)),
            'dev_nll_drop_per_seed': drops, 'dev_joint_change': float(np.mean(djoint)),
            'probe_generated_tokens': GRAD_N * GROUP * K + len(PROBE_SEEDS) * PROBE_K * BATCH * GROUP * K}


def trajectory(out, scale, env, seed, setting):
    spec = specs(out)[env]
    model = load_model(out, scale)
    ref = deepcopy(model).eval()
    for q in ref.parameters():
        q.requires_grad_(False)
    target = make_prompts(TARGET, TARGET_N, 99)
    pool = make_prompts(spec, POOL_N, 13)
    held = make_prompts(spec, HELD_N, 12)
    baseline = read(out / f'{scale}_meta.json')['start_target']
    ev = lambda m: {'target': evaluate(m, target), 'env_metrics': evaluate(m, held)}
    curve = grpo(model, ref, pool, max(STEPS), STEPS, ev, seed, batch=BATCH, group=GROUP, **setting)
    return spec.name, [{'scale': scale, 'env': spec.name, 'seed': seed, 'step': st, 'tokens': st * BATCH * GROUP * K,
                        'utility': v['target']['joint'] - baseline['joint'],
                        'token_utility': v['target']['token'] - baseline['token'], **v} for st, v in curve.items()]


def frozen_setting(out):
    if not verify_forecast(out / 'rl_setting.json'):
        raise RuntimeError('main RL and alpha probes require the frozen RL-strength choice')
    return SETTINGS[read(out / 'rl_setting.json')['chosen']]


# ------------------------------------------------------------------------------------------------- choice of strength

def f_ratio(cells):
    """Between-env variance of seed means over the mean within-env variance of a seed mean (final budget)."""
    means = np.array([np.mean(v) for v in cells.values()])
    within = np.mean([np.var(v, ddof=1) / len(v) for v in cells.values()])
    return float(means.var(ddof=1) / max(within, 1e-12)), float(means.mean())


def choose(out):
    stats = {}
    n2 = read(NIGHT2 / 'cells.json')
    cells = {}
    for c in n2:
        if c['scale'] == 'n3' and c['tokens'] == BUDGETS[-1]:
            cells.setdefault(c['env'], []).append(c['utility'])
    stats['S1'] = dict(zip(('F', 'mean_utility'), f_ratio(cells)), source='Night 2 committed n3 cells, seeds 0/1')
    for name in ('S2', 'S3'):
        cells = {}
        for e in specs(out):
            for seed in PILOT_SEEDS:
                rows = read(out / f'pilot_{name}_n3_{e.name}_seed{seed}.json')['rows']
                cells.setdefault(e.name, []).append(rows[-1]['utility'])
        stats[name] = dict(zip(('F', 'mean_utility'), f_ratio(cells)), source=f'Night 4 pilot, seeds {PILOT_SEEDS}')
    admissible = [s for s in SETTINGS if stats[s]['mean_utility'] > -0.05]
    best = max(stats[s]['F'] for s in admissible)
    chosen = next(s for s in SETTINGS if s in admissible and stats[s]['F'] >= 0.95 * best)
    receipt = {'rule': 'max F among settings whose mean final n3 utility > -5 pts; within 5% of the max, the weaker wins',
               'stats': stats, 'chosen': chosen, 'setting': SETTINGS[chosen]}
    freeze_forecast(receipt, out, 'rl_setting')
    print(json.dumps(receipt), flush=True)


# ------------------------------------------------------------------------------------------------- forecasts

def ties(values):
    top = max(values.values())
    return sorted(k for k, v in values.items() if np.isclose(v, top, rtol=0, atol=1e-12))


def fit_law_alpha(obs, alpha, ref_scales):
    """Eq. 7 plus b_alpha * z_alpha, ordinary least squares; z over training (scale, env) cells as in rl4cv."""
    base = fit_utility_model(obs, RHO_H, ref_scales=ref_scales)
    cells = {(o.scale, o.env): alpha[o.scale, o.env] for o in obs}
    a_mean, a_sd = float(np.mean(list(cells.values()))), float(np.std(list(cells.values()))) or 1.0
    row = lambda o: np.append(base.design_row(o.scale, o.budget, o.rho, o.H), (alpha[o.scale, o.env] - a_mean) / a_sd)
    train = [o for o in obs if o.budget > 0]
    beta, *_ = np.linalg.lstsq(np.vstack([row(o) for o in train]), np.array([o.utility for o in train]), rcond=None)
    model = {'beta': beta, 'base': base, 'a_mean': a_mean, 'a_sd': a_sd}
    predict = lambda scale, budget, rho, H, a: float(np.append(base.design_row(scale, budget, rho, H), (a - a_mean) / a_sd) @ beta)
    return model, predict


def load_inputs(out):
    params = {s: read(out / f'{s}_meta.json')['n_params'] for s in SCALES}
    probes = {(s, r['env']): r for s in SCALES for r in read(out / f'{s}_probe.json')}
    alph = {}
    for s in SCALES:
        rows = read(out / f'{s}_alpha.json')
        for row, a in zip(rows, alpha_from_components([r['grad_cos'] for r in rows], [r['dev_nll_drop'] for r in rows])):
            alph[params[s], row['env']] = float(a)
    return params, probes, alph


def cell_paths(out, scales):
    return sorted(p for s in scales for p in out.glob(f'main_{s}_*_seed*.json'))


def load_cells(out, scales):
    rows = [r for p in cell_paths(out, scales) for r in read(p)['rows']]
    expected = {(s, e.name, seed, b) for s in scales for e in specs(out) for seed in SEEDS for b in BUDGETS}
    if {(r['scale'], r['env'], r['seed'], r['tokens']) for r in rows} != expected or len(rows) != len(expected):
        raise ValueError(f'incomplete matrix for {scales}: {len(rows)}/{len(expected)}')
    return rows


def choices(obs, params, probes, alph, scale_name, envs):
    """Each rule's chosen set per budget at `scale_name`, from training observations `obs` (n1-n3)."""
    ref = (params['n1'], params['n3'])
    n = params[scale_name]
    law = fit_utility_model(obs, RHO_H, ref_scales=ref)
    lam, lam_pred = fit_law_alpha(obs, alph, ref)
    out, preds = {}, {}
    for name, f in [('law', lambda e, b: law.predict(n, b, probes[scale_name, e]['rho'], probes[scale_name, e]['H'])),
                    ('law+alpha', lambda e, b: lam_pred(n, b, probes[scale_name, e]['rho'], probes[scale_name, e]['H'], alph[n, e]))]:
        preds[name] = {str(b): {e: f(e, b) for e in envs} for b in BUDGETS}
        out[name] = {str(b): ties(preds[name][str(b)]) for b in BUDGETS}
    out['alpha-alone'] = {str(b): ties({e: alph[n, e] for e in envs}) for b in BUDGETS}
    small = {e: np.mean([o.utility for o in obs if o.scale == params['n3'] and o.env == e]) for e in envs}
    out['best-fixed-n3'] = {str(b): ties(small) for b in BUDGETS}
    out['uniform-random'] = {str(b): list(envs) for b in BUDGETS}
    coefs = {'law': law.coefficients(), 'law+alpha': dict(zip(['b0', 'bN', 'bC', 'b_rho', 'b_H', 'b_alpha'], map(float, lam['beta'])))}
    return out, preds, coefs


def observations(rows, params, probes, utility=None):
    cells = {}
    for r in rows:
        cells.setdefault((r['scale'], r['env'], r['tokens']), []).append(r['utility'] if utility is None else utility[r['scale'], r['env'], r['seed'], r['tokens']])
    return [Observation(params[s], e, b, float(np.mean(u)), probes[s, e]['rho'], probes[s, e]['H']) for (s, e, b), u in sorted(cells.items())]


def freeze(out):
    if list(out.glob('main_n4_*_seed*.json')):
        raise RuntimeError('n4 outcomes already exist; cannot claim a prospective freeze')
    params, probes, alph = load_inputs(out)
    rows = load_cells(out, ('n1', 'n2', 'n3'))
    envs = [e.name for e in specs(out)]
    ch, preds, coefs = choices(observations(rows, params, probes), params, probes, alph, 'n4', envs)
    inputs = cell_paths(out, ('n1', 'n2', 'n3')) + [out / f'{s}_{k}.json' for s in SCALES for k in ('probe', 'alpha', 'meta')] + [out / 'rl_setting.json']
    receipt = freeze_forecast({'primary': 'n4 allocation regret in joint exact-match points, mean over 3 budgets',
                               'train_scales': ['n1', 'n2', 'n3'], 'choices': ch, 'predictions': preds, 'coefficients': coefs,
                               'alpha_n4': {e: alph[params['n4'], e] for e in envs},
                               'input_hashes': {p.name: sha(p) for p in inputs}}, out, 'forecast_n4')
    print(json.dumps(receipt)[:2000], flush=True)


# ------------------------------------------------------------------------------------------------- report

def regrets(ch, util_n4, envs):
    """util_n4[e][b] -> mean regret over budgets for each rule; ties averaged (uniform-random = all envs)."""
    out = {}
    for rule, per_b in ch.items():
        vals = []
        for j, b in enumerate(BUDGETS):
            best = max(util_n4[e][j] for e in envs)
            vals.append(best - np.mean([util_n4[e][j] for e in per_b[str(b)]]))
        out[rule] = float(np.mean(vals))
    return out


def report(out, draws=2000):
    fpath = out / 'forecast_n4.json'
    if not verify_forecast(fpath):
        raise ValueError('forecast hash mismatch')
    fc = read(fpath)
    for name, digest in fc['input_hashes'].items():
        if sha(out / name) != digest:
            raise ValueError(f'frozen input changed: {name}')
    params, probes, alph = load_inputs(out)
    envs = [e.name for e in specs(out)]
    rows = load_cells(out, SCALES)
    write(out / 'cells.json', [{k: r[k] for k in ('scale', 'env', 'seed', 'tokens', 'utility', 'token_utility', 'last_train_kl')} for r in rows])
    lookup = {(r['scale'], r['env'], r['seed'], r['tokens']): r for r in rows}
    start = {s: (np.array(read(out / f'{s}_meta.json')['start_target']['token_hits']) == K).astype(float) for s in SCALES}
    hits = {key: (np.array(r['target']['token_hits']) == K).astype(float) - start[key[0]] for key, r in lookup.items()}
    keys = sorted(hits)
    H = np.vstack([hits[k] for k in keys])  # cells x prompts, gains per prompt
    index = {k: i for i, k in enumerate(keys)}
    train_rows = [r for r in rows if r['scale'] != 'n4']

    def evaluate_draw(seed_map, w):
        u = H @ w
        util = {k: u[index[(k[0], k[1], seed_map[k[0]][k[2]], k[3])]] for k in keys}
        obs = observations(train_rows, params, probes, util)
        ch = choices(obs, params, probes, alph, 'n4', envs)[0] if seed_map is not identity else fc['choices']
        n4 = {e: [np.mean([util['n4', e, s, b] for s in SEEDS]) for b in BUDGETS] for e in envs}
        return regrets(ch, n4, envs), n4

    identity = {s: {k: k for k in SEEDS} for s in SCALES}
    point, n4_point = evaluate_draw(identity, np.full(TARGET_N, 1 / TARGET_N))
    # Recompute frozen choices from the same data as a consistency check of the analysis code.
    check = choices(observations(train_rows, params, probes), params, probes, alph, 'n4', envs)[0]
    if check != fc['choices']:
        raise ValueError('refit on the frozen inputs does not reproduce the frozen choices')
    rng = np.random.default_rng(1604)
    boot = {r: [] for r in point}
    for _ in range(draws):
        seed_map = {s: dict(zip(SEEDS, rng.choice(SEEDS, len(SEEDS)))) for s in SCALES}
        w = rng.multinomial(TARGET_N, np.full(TARGET_N, 1 / TARGET_N)) / TARGET_N
        reg, _ = evaluate_draw(seed_map, w)
        for k, v in reg.items():
            boot[k].append(v)
    boot = {k: np.array(v) for k, v in boot.items()}
    ci = {k: [float(np.quantile(v, .025)), float(np.quantile(v, .975))] for k, v in boot.items()}
    diff = {f'law+alpha minus {k}': [float(np.quantile(boot['law+alpha'] - boot[k], q)) for q in (.025, .975)] for k in point if k != 'law+alpha'}
    diff.update({f'alpha-alone minus {k}': [float(np.quantile(boot['alpha-alone'] - boot[k], q)) for q in (.025, .975)] for k in ('uniform-random', 'law', 'best-fixed-n3')})
    if ci['law+alpha'][1] < ci['uniform-random'][0]:
        verdict = 'POSITIVE'
    elif point['law+alpha'] < point['uniform-random']:
        verdict = 'NOT ESTABLISHED (law+alpha regret below random, intervals overlap)'
    else:
        verdict = 'NO ADVANTAGE'
    # Diagnostics: how alpha and its parts rank observed n4 utility (final budget), and in-sample fits.
    from scipy.stats import spearmanr
    a4 = read(out / 'n4_alpha.json')
    final = {e: n4_point[e][-1] for e in envs}
    diag = {'spearman_final_n4': {
        'alpha': float(spearmanr([alph[params['n4'], e] for e in envs], [final[e] for e in envs])[0]),
        'grad_cos': float(spearmanr([r['grad_cos'] for r in a4], [final[r['env']] for r in a4])[0]),
        'dev_nll_drop': float(spearmanr([r['dev_nll_drop'] for r in a4], [final[r['env']] for r in a4])[0]),
        'law_prediction': float(spearmanr([fc['predictions']['law'][str(BUDGETS[-1])][e] for e in envs], [final[e] for e in envs])[0]),
        'law+alpha_prediction': float(spearmanr([fc['predictions']['law+alpha'][str(BUDGETS[-1])][e] for e in envs], [final[e] for e in envs])[0])}}
    for comp in ('grad_cos', 'dev_nll_drop'):
        pick = ties({r['env']: r[comp] for r in a4})
        diag[f'{comp}-alone regret (diagnostic, not frozen)'] = regrets({'x': {str(b): pick for b in BUDGETS}}, n4_point, envs)['x']
    diag['positive_cells'] = {s: int(sum(r['utility'] > 0 for r in rows if r['scale'] == s)) for s in SCALES}
    diag['mean_final_kl'] = {s: float(np.mean([r['last_train_kl'] for r in rows if r['scale'] == s and r['tokens'] == BUDGETS[-1]])) for s in SCALES}
    diag['logrho_alpha_corr'] = float(np.corrcoef([np.log(probes['n4', e]['rho']) for e in envs], [alph[params['n4'], e] for e in envs])[0, 1])
    diag['H_alpha_corr'] = float(np.corrcoef([probes['n4', e]['H'] for e in envs], [alph[params['n4'], e] for e in envs])[0, 1])
    result = {'verdict': verdict, 'regret_points': {k: v * 100 for k, v in point.items()},
              'ci95_points': {k: [x * 100 for x in v] for k, v in ci.items()},
              'paired_diff_ci95_points': {k: [x * 100 for x in v] for k, v in diff.items()},
              'n4_utility_points': {e: [x * 100 for x in v] for e, v in n4_point.items()},
              'choices': fc['choices'], 'coefficients': fc['coefficients'], 'diagnostics': diag, 'draws': draws}
    write(out / 'analysis.json', result)
    print(json.dumps(result, indent=1)[:6000], flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['pilot', 'choose', 'alpha', 'rl', 'freeze', 'report'])
    ap.add_argument('--out', type=Path, default=OUT)
    ap.add_argument('--scale', choices=SCALES)
    ap.add_argument('--env', type=int)
    ap.add_argument('--seed', type=int)
    ap.add_argument('--setting', choices=['S2', 'S3'])
    args = ap.parse_args()
    out = args.out
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.manual_seed(1234)
    t0 = time.time()
    if args.stage == 'pilot':
        if args.scale != 'n3' or args.seed not in PILOT_SEEDS:
            raise SystemExit('the pilot is n3 with pilot seeds only')
        name = specs(out)[args.env].name
        dest = out / f'pilot_{args.setting}_n3_{name}_seed{args.seed}.json'
        if not dest.exists():
            name, rows = trajectory(out, 'n3', args.env, args.seed, SETTINGS[args.setting])
            write(dest, {'setting': args.setting, 'rows': rows, 'seconds': time.time() - t0})
            print(f'pilot {args.setting} {name} seed={args.seed} U={rows[-1]["utility"]:+.5f}', flush=True)
    elif args.stage == 'choose':
        if not (out / 'rl_setting.json').exists():
            choose(out)
    elif args.stage == 'alpha':
        dest = out / f'{args.scale}_alpha.json'
        if not dest.exists():
            setting = frozen_setting(out)
            model = load_model(out, args.scale)
            rows = []
            for spec in specs(out):
                rows.append(alpha_probe(model, spec, setting))
                print(f'{args.scale} {spec.name} cos={rows[-1]["grad_cos"]:+.4f} dNLL={rows[-1]["dev_nll_drop"]:+.5f}', flush=True)
            write(dest, rows)
    elif args.stage == 'rl':
        if args.seed not in SEEDS:
            raise SystemExit('main seeds are 0, 1, 2')
        if args.scale == 'n4' and not verify_forecast(out / 'forecast_n4.json'):
            raise RuntimeError('n4 requires the frozen forecast')
        name = specs(out)[args.env].name
        dest = out / f'main_{args.scale}_{name}_seed{args.seed}.json'
        if not dest.exists():
            setting = frozen_setting(out)
            name, rows = trajectory(out, args.scale, args.env, args.seed, setting)
            write(dest, {'start_checkpoint_sha256': sha(out / f'start_{args.scale}.pt'), 'setting': setting,
                         'rows': rows, 'seconds': time.time() - t0})
            print(f'{args.scale} {name} seed={args.seed} U={rows[-1]["utility"]:+.5f} s={time.time() - t0:.0f}', flush=True)
    elif args.stage == 'freeze':
        freeze(out)
    elif args.stage == 'report':
        report(out)


if __name__ == '__main__':
    main()
