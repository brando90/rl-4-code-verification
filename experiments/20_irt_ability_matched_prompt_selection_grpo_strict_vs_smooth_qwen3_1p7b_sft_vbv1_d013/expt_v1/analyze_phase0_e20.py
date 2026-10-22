"""Fit and freeze Experiment 20's authorized CPU-only Phase 0b analysis, with resumable numerical audit receipts."""
from __future__ import annotations

# Set before importing NumPy/SciPy and before fork: parallel fits, one BLAS thread each.
import os
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_v] = '1'
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import datetime as dt
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import sys
import time

import numpy as np
from scipy.special import expit
from scipy.stats import rankdata, pearsonr, spearmanr, kendalltau

E20_NAME = '20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013'
E19_NAME = '19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013'
SEED, G = 20261021, 8
D = F = M = I = S = None


def initialize(repo):
    global D, F, M, I, S
    repo = Path(repo)
    sys.path[:0] = [str(repo / 'src'), str(repo / 'experiments' / E20_NAME / 'expt_v1'),
                    str(repo / 'experiments' / E19_NAME / 'expt_v1')]
    import data_e19, features_e19, irt_e20, irt_e19, stats_e20
    D, F, M, I, S = data_e19, features_e19, irt_e20, irt_e19, stats_e20


def clean(v):
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, np.ndarray)):
        return [clean(x) for x in v]
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return float(v) if np.isfinite(v) else None
    if isinstance(v, Path):
        return str(v)
    return v


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(clean(data), indent=2, sort_keys=True, allow_nan=False) + '\n')
    os.replace(tmp, path)


def csv_write(path, rows):
    rows = list(rows)
    if not rows:
        raise ValueError(f'empty audit table: {path}')
    with Path(path).open('w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows([{k: clean(v) for k, v in row.items()} for row in rows])


def stamp(out, phase, **extra):
    receipt = dict(phase=phase, utc=dt.datetime.now(dt.timezone.utc).isoformat(), pid=os.getpid(),
                   trainer_status='FAILED; unchanged', gpu_or_model_calls=0, **extra)
    write_json(Path(out) / 'progress.json', receipt)
    print(json.dumps(clean(receipt), sort_keys=True), flush=True)


def smooth_task_summary(values, observed):
    """Measured-cohort smooth summary and sharp nonconstancy bounds for one declared task."""
    values, observed = np.asarray(values, float), np.asarray(observed, bool)
    measured = values[observed]
    n_measured, n_declared = int(observed.sum()), int(observed.size)
    lower = bool(n_measured >= 2 and np.ptp(measured) > 0)
    # If observed values are constant, any missing value could differ; otherwise nonconstancy is already known.
    upper = bool(lower or n_measured < n_declared)
    return dict(
        smooth_measured=n_measured,
        smooth_declared=n_declared,
        smooth_missing=n_declared - n_measured,
        smooth_mean=float(measured.mean()) if n_measured else None,
        smooth_sd=float(measured.std(ddof=1)) if n_measured >= 2 else None,
        smooth_nonconstant=int(lower) if n_measured == n_declared else None,
        smooth_nonconstant_lower=int(lower),
        smooth_nonconstant_upper=int(upper),
        smooth_summary_scope='complete_case' if n_measured == n_declared else 'observed_cells_with_full_task_bounds',
    )


def load_inputs(repo, scores, generation_manifest, out):
    """Read train-only analytical arrays; source hashes and exact declared-cell checks fail closed."""
    initialize(repo)
    repo, scores, out = Path(repo), Path(scores), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    pin_path = repo / 'experiments' / E19_NAME / 'expt_v1/input_pins_e19.json'
    pins = json.loads(pin_path.read_text())
    relevant = ('e12_input_manifest', 'split_manifest', 'task_features', 'test_ids_guard_only', 'train_ids', 'validation_ids')
    verified = {}
    for key in relevant:
        path = repo / pins['paths'][key]
        actual = digest(path)
        if actual != pins['sha256'][key]:
            raise ValueError(f'frozen E19 input hash mismatch: {key}')
        verified[key] = {'path': str(path), 'sha256': actual, 'expected': pins['sha256'][key]}
    split = D.load_split()
    # Reuse loader guards and E12 strict definition; slice to train before any statistics or fits.
    panel = D.load_panel(split)
    J, tasks = len(split.train), split.train
    panel_k, panel_n = panel.strict[:, :J], panel.mask[:, :J]
    csv_write(out / 'panel_train_cells.csv', [dict(system=system, task_id=task, status=panel.status[i,j],
              measured=int(panel_n[i,j]), strict=panel_k[i,j] if panel_n[i,j] else None)
              for i,system in enumerate(panel.systems) for j,task in enumerate(tasks)])
    if not panel_n.any() or np.any(panel_n.sum(0) == 0):
        raise ValueError('empty panel or task with no measured panel data')
    groups = np.array([split.group[t] for t in tasks])
    if np.unique(groups).size != 400:
        raise ValueError('train split must contain 400 frozen groups')
    feature_rows = D.load_features(split)[:J]
    X, feature_names = F.design_matrix(feature_rows, np.ones(J, bool))
    if not np.isfinite(X).all():
        raise ValueError('nonfinite feature matrix')
    lookup = {t: j for j, t in enumerate(tasks)}
    strict, reward = np.full((G, J), np.nan), np.full((G, J), np.nan)
    strict_mask, reward_mask = np.zeros((G, J), bool), np.zeros((G, J), bool)
    strict_statuses, smooth_statuses, joint_statuses = Counter(), Counter(), Counter()
    missing_strict, missing_smooth, seen, rows = [], [], set(), []
    with scores.open(newline='') as fh:
        reader = csv.DictReader(fh)
        required = {'task_id', 'sample_idx', 'status', 'strict', 'factored_reward', 'partial_status',
                    'IC_tests', 'IC_proofs', 'FSC', 'generated_tokens', 'capped', 'lean_sha256', 'seed'}
        if not required <= set(reader.fieldnames or ()):
            raise ValueError(f'score schema missing {sorted(required - set(reader.fieldnames or ()))}')
        for row in reader:
            t, sample = row['task_id'], int(row['sample_idx'])
            if t not in lookup or not 0 <= sample < G:
                raise ValueError('non-train task or unexpected sample index in Phase 0 scores')
            key = (t, sample)
            if key in seen:
                raise ValueError(f'duplicate score cell: {key}')
            seen.add(key)
            rows.append(row)
            strict_statuses[row['status']] += 1
            smooth_statuses[row['partial_status']] += 1
            joint_statuses[row['status'] + '/' + row['partial_status']] += 1
            if row['FSC'] not in ('', 'unmeasured'):
                raise ValueError('unexpected measured FSC; this authorized run has no judge calls')
            j = lookup[t]
            if row['status'] == 'measured':
                a = float(row['strict'])
                if not np.isfinite(a) or a not in (0, 1):
                    raise ValueError(f'invalid strict score: {key}')
                strict[sample, j], strict_mask[sample, j] = a, True
            else:
                missing_strict.append({'task_id': t, 'sample_idx': sample, 'reason': row['status']})
            if row['partial_status'] in ('measured', 'parse_failure_zero_credit'):
                b = float(row['factored_reward'])
                if not np.isfinite(b) or not 0 <= b <= 1:
                    raise ValueError(f'invalid smooth score: {key}')
                if row['partial_status'] == 'parse_failure_zero_credit' and b != 0:
                    raise ValueError('parse-failure reward must be zero')
                reward[sample, j], reward_mask[sample, j] = b, True
            else:
                partial_note = row.get('partial_note', '').strip()
                reason = row['partial_status'] + (f': {partial_note}' if partial_note else '')
                missing_smooth.append({'task_id': t, 'sample_idx': sample, 'status': row['partial_status'],
                                       'note': partial_note, 'reason': reason})
    expected = {(t, s) for t in tasks for s in range(G)}
    absent = expected - seen
    for t, s in sorted(absent):
        missing_strict.append({'task_id': t, 'sample_idx': s, 'reason': 'missing_row'})
        missing_smooth.append({'task_id': t, 'sample_idx': s, 'status': 'missing_row',
                               'note': '', 'reason': 'missing_row'})
        strict_statuses['missing_row'] += 1
        smooth_statuses['missing_row'] += 1
    missing_any = []
    for t, s in sorted(expected):
        i, j = s, lookup[t]
        if not (strict_mask[i, j] and reward_mask[i, j]):
            missing_any.append({'task_id': t, 'sample_idx': s,
                                'strict_status': 'measured' if strict_mask[i, j] else next(
                                    (x['reason'] for x in missing_strict if x['task_id'] == t and x['sample_idx'] == s), 'missing_row'),
                                'partial_status': 'measured' if reward_mask[i, j] else next(
                                    (x['status'] for x in missing_smooth if x['task_id'] == t and x['sample_idx'] == s), 'missing_row'),
                                'partial_note': '' if reward_mask[i, j] else next(
                                    (x['note'] for x in missing_smooth if x['task_id'] == t and x['sample_idx'] == s), '')})
    audit = dict(declared_cells=J*G, received_rows=len(rows),
                 strict_measured_cells=int(strict_mask.sum()), strict_missing_cells=len(missing_strict),
                 smooth_declared_cells=J*G, smooth_measured_cells=int(reward_mask.sum()), smooth_missing_cells=len(missing_smooth),
                 measured_joint_cells=int((strict_mask & reward_mask).sum()),
                 train_tasks=J, train_groups=int(np.unique(groups).size),
                 strict_status_counts=dict(strict_statuses), smooth_status_counts=dict(smooth_statuses),
                 score_statuses=dict(joint_statuses),
                 smooth_missing_status_counts=dict(Counter(x['status'] for x in missing_smooth)),
                 smooth_missing_reason_counts=dict(Counter(x['reason'] for x in missing_smooth)),
                 panel_systems=panel.systems, panel_measured_cells=int(panel_n.sum()), panel_declared_cells=int(panel_n.size),
                 panel_status_counts=dict(Counter(panel.status[:, :J].ravel())),
                 missing_strict_cells=missing_strict, missing_smooth_cells=missing_smooth, missing_cells=missing_any,
                 smooth_missingness_likelihood=('unobserved smooth cells are ignored through an observation mask; smooth estimates are '
                                                'conditional on observed cells and missing-at-random is not established'),
                 inputs=verified, feature_names=feature_names)
    write_json(out / 'input_audit.json', audit)
    if absent or missing_strict or len(rows) != 4312 or not strict_mask.all() or not np.isfinite(strict[strict_mask]).all():
        raise ValueError('Phase 0 strict scoring incomplete: see input_audit.json; no strict fitted result is released')
    # Link exactly to the previously saved generation cells, including explicit no-Lean cells.
    with Path(generation_manifest).open(newline='') as fh:
        generation_rows = list(csv.DictReader(fh))
        generation = {(r['task_id'], int(r['sample_idx'])): r for r in generation_rows}
    if len(generation_rows) != 4312 or set(generation) != expected:
        raise ValueError('saved generation manifest does not cover exactly 539 x 8')
    for row in rows:
        old = generation[(row['task_id'], int(row['sample_idx']))]
        for key in ('lean_sha256', 'seed', 'generated_tokens', 'capped'):
            if row[key] != old[key]:
                raise ValueError(f'changed saved generation field {key}: {row["task_id"]}/{row["sample_idx"]}')
    # E05 all-task files are filtered by train membership BEFORE parsing outcomes.
    base_k, base_n, base_names, base_audit = [], [], [], []
    for path in sorted((repo / 'experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/expt_v1/results').glob('per_task_*_g8.csv')):
        ks, ns, seen_base = np.zeros(J), np.zeros(J), set()
        for r in csv.DictReader(path.open(newline='')):
            if r['task_id'] not in lookup:
                continue
            t = r['task_id']
            if t in seen_base:
                raise ValueError('duplicate train row in E05 counts')
            seen_base.add(t)
            k, n = float(r['k_kernel_binary']), float(r['samples_present'])
            if not np.isfinite([k, n]).all() or not 0 <= k <= n <= G or k != int(k) or n != int(n):
                raise ValueError('invalid E05 binomial count')
            ks[lookup[t]], ns[lookup[t]] = k, n
        if len(seen_base) != J or not ns.any():
            raise ValueError('missing/empty E05 train count table')
        base_k.append(ks); base_n.append(ns); base_names.append(path.stem)
        base_audit.append(dict(path=str(path), sha256=digest(path), successes=int(ks.sum()), trials=int(ns.sum())))
    if len(base_k) != 3:
        raise ValueError('expected the three E05 Base-model count tables')
    provenance = dict(inputs=verified, scores={'path': str(scores), 'sha256': digest(scores)},
                      generation_manifest={'path': str(generation_manifest), 'sha256': digest(generation_manifest)},
                      e05=base_audit, software={})
    for path in (Path(__file__), repo / 'experiments' / E20_NAME / 'PROTOCOL.md',
                 repo / 'experiments' / E20_NAME / 'expt_v1/irt_e20.py',
                 repo / 'experiments' / E20_NAME / 'expt_v1/stats_e20.py',
                 repo / 'experiments' / E19_NAME / 'expt_v1/irt_e19.py',
                 repo / 'experiments' / E19_NAME / 'expt_v1/data_e19.py',
                 repo / 'experiments' / E19_NAME / 'expt_v1/features_e19.py', repo / 'src/rl4cv/forecast.py'):
        provenance['software'][str(path)] = digest(path)
    summary_path = scores.with_name('phase0_summary_e20.json')
    if summary_path.exists():
        score_summary = json.loads(summary_path.read_text())
        provenance['score_summary'] = {'path': str(summary_path), 'sha256': digest(summary_path)}
        audit['scorer_adapter_strict_disagreements'] = score_summary.get('counts', {}).get('adapter_strict_disagrees', 0)
    else:
        audit['scorer_adapter_strict_disagreements'] = 'unavailable: score summary not supplied'
    write_json(out / 'input_audit.json', audit)
    identity = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    pins_out = out / 'input_pins_e20.json'
    frozen_inputs = dict(identity=identity, **provenance)
    if pins_out.exists() and json.loads(pins_out.read_text()) != frozen_inputs:
        raise ValueError('inputs/software changed in this output directory; preserve it and use a new directory')
    write_json(pins_out, frozen_inputs)
    task_rows = []
    for j, t in enumerate(tasks):
        smooth = smooth_task_summary(reward[:, j], reward_mask[:, j])
        measured_cat = np.array([M.factored_category(v) for v in reward[:, j][reward_mask[:, j]]], int)
        category_lower = bool(measured_cat.size >= 2 and np.ptp(measured_cat) > 0)
        smooth.update(smooth_category_nonconstant=(int(category_lower) if smooth['smooth_missing'] == 0 else None),
                      smooth_category_nonconstant_lower=int(category_lower),
                      smooth_category_nonconstant_upper=int(category_lower or smooth['smooth_missing'] > 0))
        task_rows.append(dict(task_id=t, group_id=groups[j], k_strict=int(strict[:, j].sum()), n=G, n_strict=G,
                              active=int(0 < strict[:, j].sum() < G), **smooth))
    csv_write(out / 'phase0_tasks.csv', task_rows)
    return dict(tasks=tasks, groups=groups, X=X, feature_names=feature_names, panel_k=panel_k, panel_n=panel_n,
                systems=panel.systems, strict=strict, strict_mask=strict_mask, reward=reward, reward_mask=reward_mask,
                smooth_missing_status_counts=dict(Counter(x['status'] for x in missing_smooth)),
                smooth_missing_reason_counts=dict(Counter(x['reason'] for x in missing_smooth)),
                k_sp=np.where(strict_mask, strict, 0).sum(0), n_sp=strict_mask.sum(0).astype(float),
                base_k=np.array(base_k), base_n=np.array(base_n), base_names=base_names, identity=identity)


def fit_meta(fit):
    return {k: clean(v) for k, v in fit.items() if k not in ('x', 'X', 'b', 'cuts')}


def fit_job(job):
    """One immutable numerical fit; input hash protects reuse, arrays reconstructed from JSON."""
    path = Path(job['cache'])
    if path.exists():
        saved = json.loads(path.read_text())
        if saved['identity'] != job['identity']:
            raise ValueError(f'cached fit input mismatch: {path}')
        fit = saved['fit']
        for key in ('x', 'X', 'b', 'cuts'):
            if key in fit and fit[key] is not None:
                fit[key] = np.array(fit[key], float)
        return fit
    started = time.monotonic()
    if job['kind'] == 'count':
        fit = M.fit_2pl_counts(job['K'], job['N'], X=job['X'], sigma_e=job['sigma_e'],
                              slope_sd=job['slope_sd'], fixed_slope=job.get('fixed_slope', False),
                              grid=I.BASE, check=I.CHECK)
    else:
        fit = I.fit_two_skill(job['ys'], job['ms'], job['cat'], job['mc'], 5, tied=job['tied'],
                              slope_sd=job['slope_sd'], sigma_e=job['sigma_e'])
    fit['elapsed_seconds'] = time.monotonic() - started
    write_json(path, dict(identity=job['identity'], fit=fit))
    return fit


def job_for(out, identity, name, **kwargs):
    # Scientific arguments are all represented, preventing reuse across masked folds or priors.
    h = hashlib.sha256(identity.encode())
    for key, value in sorted(kwargs.items()):
        h.update(key.encode())
        if isinstance(value, np.ndarray):
            h.update(str(value.shape).encode()); h.update(str(value.dtype).encode()); h.update(value.tobytes())
        else:
            h.update(json.dumps(value, sort_keys=True).encode())
    return dict(cache=str(Path(out) / 'fits' / f'{name}.json'), identity=h.hexdigest(), **kwargs)


def run_jobs(jobs, repo, out, phase, workers):
    results = {}
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context('fork'), initializer=initialize, initargs=(str(repo),)) as pool:
        futures = {pool.submit(fit_job, job): key for key, job in jobs.items()}
        for future in as_completed(futures):
            key = futures[future]
            results[key] = future.result()
            stamp(out, phase, completed=len(results), declared=len(jobs), last_fit=key,
                  last_converged=results[key]['converged'])
    return results


def prior_search(data, K, N, tag, repo, out, workers):
    """Exactly 20 prior pairs x 5 folds separately for each 2PL; 1PL uses five residual scales."""
    folds = M.cell_folds(K.shape[0], data['groups'])
    if tag == 'with_e05':
        # Preserve the hash identity of the start respondent (11) across the sensitivity.
        P, B = len(data['systems']), len(data['base_names'])
        folds = folds[list(range(P)) + list(range(P+1, P+B+1)) + [P]]
    jobs, keys = {}, []
    for family, X in (('random_intercept', I.random_intercept(K.shape[1])), ('explanatory', data['X'])):
        for fixed in (False, True):
            for sa in ((1.0,) if fixed else M.SLOPE_GRID):
                for se in M.SIGMA_GRID:
                    for fold in range(5):
                        key = f'{tag}_cv_{family}_{"1pl" if fixed else "2pl"}_a{sa}_e{se}_f{fold}'
                        held = folds == fold
                        jobs[key] = job_for(out, data['identity'], key, kind='count', K=K * ~held, N=N * ~held,
                                            X=X, sigma_e=se, slope_sd=sa, fixed_slope=fixed)
                        keys.append((key, family, fixed, sa, se, fold))
    fits = run_jobs(jobs, repo, out, f'{tag}:prior_search', workers)
    table, fold_table = [], []
    chosen = {}
    for family in ('random_intercept', 'explanatory'):
        for fixed in (False, True):
            for sa in ((1.0,) if fixed else M.SLOPE_GRID):
                for se in M.SIGMA_GRID:
                    losses, trials, oks = [], [], []
                    for key, fam, fi, a, e, fold in keys:
                        if (fam, fi, a, e) != (family, fixed, sa, se):
                            continue
                        fit, held = fits[key], folds == fold
                        post = M.posterior_theta(fit, K * ~held, N * ~held)
                        p = np.clip(M.predictive_p(fit, post), 1e-12, 1-1e-12)
                        loss = -float((K[held]*np.log(p[held]) + (N-K)[held]*np.log1p(-p[held])).sum())
                        trial = float(N[held].sum())
                        if trial <= 0:
                            raise ValueError('empty held-out CV fold')
                        losses.append(loss); trials.append(trial); oks.append(fit['converged'])
                        fold_table.append({**fit_meta(fit), 'family': family, 'fixed_slope': fixed, 'slope_sd': sa,
                                           'sigma_e': se, 'fold': fold, 'log_loss': loss/trial, 'trials': trial})
                    table.append(dict(family=family, fixed_slope=fixed, slope_sd=sa, sigma_e=se,
                                      log_loss=sum(losses)/sum(trials), trials=sum(trials), converged_folds=sum(oks), folds=5))
            eligible = [r for r in table if r['family'] == family and r['fixed_slope'] == fixed and r['converged_folds'] == 5]
            name = family + ('_1pl' if fixed else '')
            chosen[name] = min(eligible, key=lambda r: (r['log_loss'], -r['sigma_e'], -r['slope_sd'])) if eligible else None
    csv_write(Path(out) / f'{tag}_cv_folds.csv', fold_table)
    csv_write(Path(out) / f'{tag}_cv_grid.csv', table)
    write_json(Path(out) / f'{tag}_priors.json', chosen)
    return chosen


def fast_auc(p, y):
    y = np.asarray(y, bool)
    n1, n0 = y.sum(), (~y).sum()
    return float((rankdata(p)[y].sum() - n1*(n1+1)/2)/(n1*n0)) if n1 and n0 else float('nan')


def summarize_boot(point, boot, null=None):
    finite = np.asarray(boot)[np.isfinite(boot)]
    if not len(finite):
        return dict(point=point, lo=None, hi=None, valid_draws=0, requested_draws=len(boot), p_two_sided=None)
    lo, hi = np.percentile(finite, [2.5, 97.5])
    p = None if null is None else min(1.0, max(1/len(boot), 2*min(np.mean(finite <= null), np.mean(finite >= null))))
    return dict(point=point, lo=lo, hi=hi, valid_draws=len(finite), requested_draws=len(boot), p_two_sided=p, null=null)


def gate(data, K, N, priors, tag, repo, out, workers):
    """Five grouped held-out-start folds, with check-grid gating and every comparator retained."""
    J, sp = K.shape[1], K.shape[0]-1
    folds = M.task_folds(data['groups'])
    jobs, predictions, strict_predictions = {}, {}, {}
    fit_records = []
    names = ('random_intercept', 'explanatory', 'random_intercept_1pl', 'explanatory_1pl', 'features_only')
    for name in names:
        predictions[name] = np.full(J, np.nan)
    predictions['baseline'] = np.full(J, np.nan)
    y = ((data['k_sp'] > 0) & (data['k_sp'] < G)).astype(float)
    for f in range(5):
        held = folds == f
        pbar = (data['k_sp'][~held].sum()+1)/(data['n_sp'][~held].sum()+2)
        predictions['baseline'][held] = M.forecast_active(pbar)
        for name in names:
            family = 'explanatory' if name == 'features_only' else name
            pr = priors[family]
            if pr is None:
                continue
            kk, nn = K.copy(), N.copy()
            kk[sp, held], nn[sp, held] = 0, 0
            X = data['X'] if family.startswith('explanatory') else I.random_intercept(J)
            if name == 'features_only':
                # Held-out item responses removed from ALL persons. Feature scaling remains the fixed train moments.
                kk, nn, X = kk[:, ~held], nn[:, ~held], X[~held]
            key = f'{tag}_g0_{name}_f{f}'
            jobs[key] = job_for(out, data['identity'], key, kind='count', K=kk, N=nn, X=X,
                                sigma_e=pr['sigma_e'], slope_sd=pr['slope_sd'], fixed_slope=name.endswith('_1pl'))
    fits = run_jobs(jobs, repo, out, f'{tag}:G0', workers)
    for f in range(5):
        held = folds == f
        for name in names:
            key = f'{tag}_g0_{name}_f{f}'
            if key not in fits:
                continue
            fit, job = fits[key], jobs[key]
            post = M.posterior_theta(fit, job['K'], job['N'])[sp]
            mean, sd = I.eap(post[None, :])
            fit_records.append(dict(fold=f, model=name, theta=mean[0], theta_sd=sd[0], **fit_meta(fit)))
            if not fit['converged']:
                continue
            curves = I.new_item_curves(fit, data['X'][held], int(held.sum())) if name == 'features_only' else M.item_curves(fit, np.flatnonzero(held))
            predictions[name][held] = M.predictive_active(curves, post)
            strict_predictions.setdefault(name, np.full(J, np.nan))[held] = curves @ post
    panel_rate = data['panel_k'].sum(0)/data['panel_n'].sum(0)
    models = {}
    for name, p in predictions.items():
        if not np.isfinite(p).all():
            models[name] = dict(status='unavailable: prior or fit convergence gate failed', predicted_tasks=int(np.isfinite(p).sum()))
            continue
        models[name] = dict(status='available', auc=fast_auc(p, y), log_loss=S.log_loss(p, y), ece=S.ece(p, y),
                            predicted_active_share=float(p.mean()), observed_active_share=float(y.mean()),
                            mean_absolute_error=float(np.abs(p-y).mean()), mean_bias=float((p-y).mean()))
        if name in strict_predictions:
            models[name].update(predicted_strict_rate=float(strict_predictions[name].mean()),
                                 observed_strict_rate=float(data['k_sp'].mean()/G))
    models['panel_strict_rate'] = dict(status='available: ranking only', auc=fast_auc(panel_rate, y))
    candidates = [name for name in ('random_intercept', 'explanatory') if models[name]['status'] == 'available']
    # Both prespecified families must be numerically evaluable; a failed family cannot be silently dropped.
    selected = min(candidates, key=lambda x: (models[x]['log_loss'], x != 'random_intercept')) if len(candidates) == 2 else None
    gate_result = dict(status='unavailable' if selected is None else 'evaluated', selected_model=selected,
                       auc_threshold=0.70, threshold_source='E20 PROTOCOL section 3; E13 F2',
                       passed=False, baseline_log_loss=models['baseline']['log_loss'])
    if selected:
        gate_result.update(auc=models[selected]['auc'], log_loss=models[selected]['log_loss'],
                           passed=bool(models[selected]['auc'] >= .70 and models[selected]['log_loss'] < models['baseline']['log_loss']))
    # Cache bootstrap too: its deterministic inputs are a function of the completed numerical fits.
    boot_path = Path(out) / f'{tag}_g0_bootstrap.json'
    boot_identity = hashlib.sha256(json.dumps(clean(dict(identity=data['identity'], predictions=predictions)), sort_keys=True).encode()).hexdigest()
    if boot_path.exists() and json.loads(boot_path.read_text()).get('identity') == boot_identity:
        intervals = json.loads(boot_path.read_text())['intervals']
    else:
        rng = np.random.default_rng(SEED)
        _, inv = np.unique(data['groups'], return_inverse=True)
        members = [np.flatnonzero(inv == g) for g in range(inv.max()+1)]
        valid = [n for n in predictions if np.isfinite(predictions[n]).all()]
        vals = {n: {metric: [] for metric in ('auc', 'log_loss', 'ece', 'predicted_active_share', 'observed_active_share', 'mean_bias', 'mean_absolute_error', 'log_loss_gain_vs_baseline', 'auc_minus_panel')} for n in valid}
        panel_aucs = []
        for b in range(10000):
            idx = np.concatenate([members[g] for g in rng.integers(0, len(members), len(members))])
            yy = y[idx]; bp = predictions['baseline'][idx]
            ap = fast_auc(panel_rate[idx], yy); panel_aucs.append(ap)
            baseline_ll = S.log_loss(bp, yy)
            for name in valid:
                p = predictions[name][idx]; au = fast_auc(p, yy); ll = S.log_loss(p, yy)
                values = (au, ll, S.ece(p, yy), p.mean(), yy.mean(), (p-yy).mean(), np.abs(p-yy).mean(), baseline_ll-ll, au-ap)
                for metric, val in zip(vals[name], values):
                    vals[name][metric].append(val)
            if (b+1) % 1000 == 0:
                stamp(out, f'{tag}:bootstrap', completed=b+1, declared=10000)
        intervals = {}
        for name in valid:
            intervals[name] = {}
            for metric, samples in vals[name].items():
                if metric == 'log_loss_gain_vs_baseline':
                    point, null = models['baseline']['log_loss'] - models[name]['log_loss'], 0.0
                elif metric == 'auc_minus_panel':
                    point, null = models[name]['auc'] - models['panel_strict_rate']['auc'], 0.0
                else:
                    point, null = models[name][metric], (.70 if metric == 'auc' else None)
                intervals[name][metric] = summarize_boot(point, samples, null)
        intervals['panel_strict_rate'] = {'auc': summarize_boot(models['panel_strict_rate']['auc'], panel_aucs)}
        write_json(boot_path, dict(identity=boot_identity, intervals=intervals, draws=10000, seed=SEED,
                                  unit='D-013 train task group', limits='conditional on fitted/selected models; not refit or nested-selection uncertainty'))
    result = dict(gate=gate_result, models=models, intervals=intervals, convergence=fit_records,
                   tasks=J, groups=int(np.unique(data['groups']).size), selected_model=selected)
    write_json(Path(out) / f'{tag}_g0.json', result)
    csv_write(Path(out) / f'{tag}_g0_predictions.csv', [dict(task_id=t, group_id=data['groups'][j], fold=int(folds[j]),
              observed_active=y[j], panel_rate=panel_rate[j], **{f'active_{n}': p[j] for n,p in predictions.items()},
              **{f'strict_{n}': p[j] for n,p in strict_predictions.items()}) for j,t in enumerate(data['tasks'])])
    return result


def final_fits(data, K, N, priors, tag, repo, out, workers):
    jobs = {}
    for name, pr in priors.items():
        if pr is None:
            continue
        key = f'{tag}_final_{name}'
        jobs[name] = job_for(out, data['identity'], key, kind='count', K=K, N=N,
                            X=data['X'] if name.startswith('explanatory') else I.random_intercept(K.shape[1]),
                            sigma_e=pr['sigma_e'], slope_sd=pr['slope_sd'], fixed_slope=name.endswith('_1pl'))
    fits = run_jobs(jobs, repo, out, f'{tag}:final_fits', workers)
    for name, fit in fits.items():
        if not fit['converged']:
            continue
        a, d = M.item_params(fit)
        post = M.posterior_theta(fit, K, N)[-1]
        theta, sd = I.eap(post[None, :])
        p = M.predictive_p(fit, post[None, :])[0]
        active = M.predictive_active(M.item_curves(fit, np.arange(K.shape[1])), post)
        fit.update(theta0=float(theta[0]), theta0_sd=float(sd[0]), p_strict=p, p_active=active)
        csv_write(Path(out) / f'{tag}_items_{name}.csv', [dict(task_id=t, a=a[j], d=d[j], difficulty=-d[j]/a[j],
                  p_strict=p[j], p_active=active[j]) for j,t in enumerate(data['tasks'])])
    write_json(Path(out) / f'{tag}_final_fit_summary.json', {name: fit_meta(fit) for name, fit in fits.items()})
    return fits


def paired_cell_count(ms, mc, pseudo, target):
    """Number of requested cells with both strict and smooth outcomes observed."""
    paired = (np.asarray(ms) > 0) & (np.asarray(mc) > 0)
    return int(paired[np.ix_(np.asarray(pseudo, int), np.asarray(target, int))].sum())


def joint_log_score(fit, ys, ms, cat, mc, target, pseudo, score_mask):
    """Log score of each held-out strict/category PAIR, integrating their conditional dependence."""
    grid = I.Grid(*fit['grid'])
    par = I.two_skill_params(fit['x'], fit['n_items'], 5, fit['tied'])
    oh = I.onehot_categories(cat, mc, 5)
    ls, lf = I.two_skill_node_logliks(par, ys, ms, oh, grid.nodes)
    _, joint, post_s, _, _ = I.two_skill_posterior(par, ls, lf, grid)
    # For an untied posterior first integrate strict nodes, leaving a per-item graded-node measure.
    total = 0.0
    for r in pseudo:
        paired_target = np.asarray(target)[np.asarray(score_mask[r, target], bool)]
        if not len(paired_target):
            continue
        ac = expit(par['a'][paired_target, None]*grid.nodes + par['d'][paired_target, None])
        pc, _ = I.grm_cat_probs(par['b'][paired_target], par['cuts'][paired_target], grid.nodes)
        prob_s = np.where(ys[r, paired_target, None] == 1, ac, 1-ac)
        prob_c = np.take_along_axis(
            pc,
            np.broadcast_to(cat[r, paired_target, None, None].astype(int), (len(paired_target), grid.count, 1)),
            axis=2,
        )[:, :, 0]
        weighted = prob_s * post_s[r] if joint is None else prob_s @ joint[r]
        prob = np.sum(weighted * prob_c, axis=1)
        total += float(np.log(np.clip(prob, 1e-300, 1)).sum())
    return total


def smooth_analysis(data, strict_fit, pr, repo, out):
    # Category zero is only a storage placeholder where mc=0; it contributes no likelihood.
    reward_mask = np.asarray(data['reward_mask'], bool)
    cat = np.zeros(data['reward'].shape, int)
    cat[reward_mask] = np.array([M.factored_category(v) for v in data['reward'][reward_mask]], int)
    mc, zeros = reward_mask.astype(float), np.zeros_like(cat, float)
    job = job_for(out, data['identity'], 'smooth_graded', kind='two_skill', ys=zeros, ms=zeros, cat=cat, mc=mc,
                  tied=True, slope_sd=pr['slope_sd'], sigma_e=pr['sigma_e'])
    stamp(out, 'smooth_graded_fit')
    fit = fit_job(job)
    measured_by_task = reward_mask.sum(0)
    complete_task = measured_by_task == G
    observed_category_lower = np.array([
        reward_mask[:, j].sum() >= 2 and np.ptp(cat[:, j][reward_mask[:, j]]) > 0 for j in range(cat.shape[1])
    ], bool)
    observed_exact_lower = np.array([
        reward_mask[:, j].sum() >= 2 and np.ptp(data['reward'][:, j][reward_mask[:, j]]) > 0 for j in range(cat.shape[1])
    ], bool)
    observed_category_upper = observed_category_lower | ~complete_task
    observed_exact_upper = observed_exact_lower | ~complete_task
    report = dict(fit=fit_meta(fit), status='available' if fit['converged'] else 'unavailable: convergence gate failed',
                   pseudo_respondents=8, real_start_policies=1,
                   identifiability='pseudo-respondents are sample indices of one policy; no across-system shared-skill claim',
                   smooth_declared_cells=int(reward_mask.size), smooth_measured_cells=int(reward_mask.sum()),
                   smooth_missing_cells=int(reward_mask.size-reward_mask.sum()),
                   smooth_missing_status_counts=data['smooth_missing_status_counts'],
                   smooth_missing_reason_counts=data['smooth_missing_reason_counts'],
                   tasks_with_any_smooth=int((measured_by_task > 0).sum()), smooth_complete_case_tasks=int(complete_task.sum()),
                   observed_category_nonconstant_tasks_lower=int(observed_category_lower.sum()),
                   observed_category_nonconstant_tasks_upper=int(observed_category_upper.sum()),
                   observed_exact_nonconstant_tasks_lower=int(observed_exact_lower.sum()),
                   observed_exact_nonconstant_tasks_upper=int(observed_exact_upper.sum()),
                   smooth_missingness_likelihood=('unobserved smooth cells are ignored through the observation mask; estimates are '
                                                  'conditional on observed smooth cells and missing-at-random is not established'),
                   selection_limitation=('the declaration adapter can leave smooth reward unresolved for outcome-dependent source '
                                         'structures; the observed smooth cohort may therefore be selected'))
    if fit['converged']:
        par = I.two_skill_params(fit['x'], fit['n_items'], 5, True)
        pred = I.two_skill_predict(fit, zeros, zeros, cat, mc, np.arange(cat.shape[1]))
        # Each of the eight sample-index respondents has its own ability posterior.
        active = 1 - np.prod(pred['cat_probs'], axis=0).sum(axis=1)
        csv_write(Path(out) / 'smooth_items.csv', [dict(
                  task_id=t, smooth_measured=int(measured_by_task[j]), smooth_declared=G,
                  b=par['b'][j], **{f'cut_{c+1}': par['cuts'][j,c] for c in range(4)},
                  first_location=-par['cuts'][j,0]/par['b'][j], p_nonconstant_categories=active[j],
                  observed_category_nonconstant=(int(observed_category_lower[j]) if complete_task[j] else None),
                  observed_category_nonconstant_lower=int(observed_category_lower[j]),
                  observed_category_nonconstant_upper=int(observed_category_upper[j]),
                  observed_exact_nonconstant=(int(observed_exact_lower[j]) if complete_task[j] else None),
                  observed_exact_nonconstant_lower=int(observed_exact_lower[j]),
                  observed_exact_nonconstant_upper=int(observed_exact_upper[j]))
                  for j,t in enumerate(data['tasks'])])
        complete_den = int(complete_task.sum())
        report.update(predicted_category_nonconstant_share=active.mean(),
                      observed_category_nonconstant_share_lower=observed_category_lower.mean(),
                      observed_category_nonconstant_share_upper=observed_category_upper.mean(),
                      observed_exact_nonconstant_share_lower=observed_exact_lower.mean(),
                      observed_exact_nonconstant_share_upper=observed_exact_upper.mean(),
                      observed_category_nonconstant_complete_case_share=(
                          observed_category_lower[complete_task].mean() if complete_den else None),
                      observed_exact_nonconstant_complete_case_share=(
                          observed_exact_lower[complete_task].mean() if complete_den else None),
                      forecast_scope='posterior replication in ordinal categories; a lower bound on exact smooth nonconstancy; within-bin differences unidentifiable',
                      forecast_status='in-sample posterior prediction, not a prospective claim about already-scored Phase 0')
        if strict_fit and strict_fit['converged']:
            a,d = M.item_params(strict_fit); difficulty=-d/a
            # E19's cuts enter b*theta+cut; ability-scale threshold is -cut/b. Retain literal cut as audit.
            correlations = {}
            for name, threshold in (('first_threshold_ability_scale', -par['cuts'][:,0]/par['b']), ('first_cut_logit_parameter', par['cuts'][:,0])):
                funcs = dict(pearson=pearsonr, spearman=spearmanr, kendall=kendalltau)
                points = {k: float(fn(difficulty, threshold).statistic) for k,fn in funcs.items()}
                boots = {k: [] for k in funcs}
                rng = np.random.default_rng(SEED)
                for _ in range(1000):
                    idx = S.group_bootstrap_indices(data['groups'], rng)
                    for k,fn in funcs.items():
                        boots[k].append(float(fn(difficulty[idx], threshold[idx]).statistic))
                correlations[name] = {k: summarize_boot(points[k], boots[k]) for k in funcs}
            report['difficulty_correlations'] = correlations
            report['correlation_bootstrap'] = dict(draws=1000, seed=SEED, unit='D-013 train item group',
                groups=int(np.unique(data['groups']).size), limitations='conditional on fitted item parameters; no model refitting; p-values not computed')
    write_json(Path(out) / 'smooth_analysis.json', report)
    # Strict panel observations plus eight start-policy sample rows. The aggregate start-policy row is NOT duplicated.
    ys = np.vstack([data['panel_k'], data['strict']])
    ms = np.vstack([data['panel_n'], data['strict_mask'].astype(float)])
    cc = np.vstack([np.zeros_like(data['panel_k'], int), cat])
    mc = np.vstack([np.zeros_like(data['panel_n']), reward_mask.astype(float)])
    pseudo = np.arange(len(data['systems']), ys.shape[0])
    pair_mask = (ms > 0) & (mc > 0)
    declared_pairs = int(len(pseudo) * len(data['tasks']))
    observed_pairs = int(pair_mask[pseudo].sum())
    dim = dict(status='running', full_fits={}, fold_fits=[],
               paired_cells_declared=declared_pairs, paired_cells_observed=observed_pairs,
               limitation='one real start policy with both channels; sample indices are pseudo-respondents',
               selection_limitation=('held-out likelihood scores only cells where both strict and smooth were observed; it is '
                                     'conditional on that selected cohort and missing-at-random is not established'))
    for tied in (True, False):
        key = f'dimensionality_full_{"tied" if tied else "untied"}'
        stamp(out, key)
        fit2 = fit_job(job_for(out, data['identity'], key, kind='two_skill', ys=ys, ms=ms, cat=cc, mc=mc,
                              tied=tied, slope_sd=pr['slope_sd'], sigma_e=pr['sigma_e']))
        dim['full_fits']['tied' if tied else 'untied'] = fit_meta(fit2)
        write_json(Path(out) / 'dimensionality.json', dim)
    if not all(f['converged'] for f in dim['full_fits'].values()):
        dim['status'] = 'unavailable: full-fit convergence gate failed'
        write_json(Path(out) / 'dimensionality.json', dim)
        return report, dim
    folds = M.task_folds(data['groups'])
    totals, cells, all_ok = dict(tied=0., untied=0.), 0, True
    for f in range(5):
        held = np.flatnonzero(folds == f)
        ms2, mc2 = ms.copy(), mc.copy()
        ms2[np.ix_(pseudo,held)] = 0; mc2[np.ix_(pseudo,held)] = 0
        for tied in (True, False):
            name = 'tied' if tied else 'untied'
            key = f'dimensionality_fold{f}_{name}'
            stamp(out, key)
            fit2 = fit_job(job_for(out, data['identity'], key, kind='two_skill', ys=ys, ms=ms2, cat=cc, mc=mc2,
                                  tied=tied, slope_sd=pr['slope_sd'], sigma_e=pr['sigma_e']))
            row = dict(fold=f, model=name, **fit_meta(fit2))
            if fit2['converged']:
                row['paired_cells_scored'] = paired_cell_count(ms, mc, pseudo, held)
                row['joint_log_likelihood'] = joint_log_score(fit2, ys, ms2, cc, mc2, held, pseudo, pair_mask)
                totals[name] += row['joint_log_likelihood']
            else:
                all_ok = False
            dim['fold_fits'].append(row)
            write_json(Path(out) / 'dimensionality.json', dim)
        cells += paired_cell_count(ms, mc, pseudo, held)
        if not all_ok:
            break  # the descriptive comparison is unavailable; do not spend on remaining failed-gate folds
    dim.update(status='available' if all_ok else 'unavailable: held-out convergence gate failed', paired_cells_scored=cells,
                joint_log_likelihood=totals if all_ok else None,
                untied_minus_tied=totals['untied']-totals['tied'] if all_ok else None,
                likelihood_definition=('sum of log posterior-predictive joint(strict outcome, ordinal category) per held-out '
                                       'pseudo-respondent/item cell with both outcomes observed'))
    write_json(Path(out) / 'dimensionality.json', dim)
    return report, dim


def freeze_parameters(data, fit, g0, out, freeze_dir):
    from rl4cv.forecast import freeze_forecast, verify_forecast
    if not fit or not fit['converged'] or g0['selected_model'] is None:
        return dict(status='unavailable: numerical convergence or model selection')
    a, d = M.item_params(fit)
    payload = clean(dict(experiment=E20_NAME, scope='parameters and posterior forecasts for future draws; observed Phase 0 excluded from prospective claims',
                        input_identity=data['identity'], model=g0['selected_model'], G0=g0['gate'], trainer_status='FAILED; no training authorized',
                        task_ids=data['tasks'], a=a, d=d, theta0=fit['theta0'], theta0_sd=fit['theta0_sd'],
                        p_strict=fit['p_strict'], p_active=fit['p_active'],
                        probability_definition='p_strict and p_active integrate the start ability posterior',
                        p_strict_at_theta0=expit(a*fit['theta0']+d),
                        p_active_at_theta0=M.forecast_active(expit(a*fit['theta0']+d)),
                        hypothesis_forecasts='H1-H4 numerical treatment-effect forecasts not estimable from Phase 0; separate pretraining registration required if training is ever reauthorized',
                        grid=dict(lo=-12, hi=12, count=1201), check_grid=dict(lo=-18, hi=18, count=4801), gradient_tolerance=1e-4))
    path = Path(freeze_dir) / 'phase0_item_parameters_e20.json'
    if path.exists():
        if not verify_forecast(path) or json.loads(path.read_text()) != payload:
            raise ValueError('existing frozen forecast differs or fails native verification; append-only preservation required')
        receipt = dict(status='already frozen; verified', file=str(path))
    else:
        receipt = freeze_forecast(payload, freeze_dir, 'phase0_item_parameters_e20', outcomes_observed=False)
        if not verify_forecast(path):
            raise ValueError('native forecast verification failed')
        receipt.update(status='frozen and verified', file=str(path))
    write_json(Path(out) / 'freeze_receipt.json', receipt)
    return receipt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=Path.cwd())
    ap.add_argument('--scores', type=Path, required=True)
    ap.add_argument('--generation-manifest', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--freeze-dir', type=Path)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--inputs-only', action='store_true', help='validate and pin inputs without any fits')
    ap.add_argument('--phase', choices=('strict', 'smooth', 'all'), default='all', help='resume independent stages with shared fit cache')
    args = ap.parse_args()
    if not 1 <= args.workers <= 16:
        ap.error('--workers must be 1..16')
    args.repo = args.repo.resolve(); args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    generation = args.generation_manifest or args.repo / 'experiments' / E20_NAME / 'expt_v1/results/phase0_cells_unscored.csv'
    data = load_inputs(args.repo, args.scores, generation, args.out)
    stamp(args.out, 'inputs_verified', cells=4312)
    if args.inputs_only:
        return 0
    all_results, fits_by_tag, priors_by_tag = {}, {}, {}
    for tag, include_base in (('primary', False), ('with_e05', True)):
        pk = np.vstack([data['panel_k'], data['base_k']]) if include_base else data['panel_k']
        pn = np.vstack([data['panel_n'], data['base_n']]) if include_base else data['panel_n']
        K, N = np.vstack([pk, data['k_sp']]), np.vstack([pn, data['n_sp']])
        priors = prior_search(data, K, N, tag, args.repo, args.out, args.workers)
        priors_by_tag[tag] = priors
        g0 = gate(data, K, N, priors, tag, args.repo, args.out, args.workers)
        fits = final_fits(data, K, N, priors, tag, args.repo, args.out, args.workers)
        fits_by_tag[tag], all_results[tag] = fits, g0
    # E05 selection language has no numerical alteration threshold; retain primary and both sensitivity outcomes.
    sensitivity = dict(primary='11 E12 systems plus start policy', alternative='primary plus three E05 Base models',
                       selection_rule='No outcome-driven replacement: substantive fit-change threshold was not preregistered; report both.',
                       primary_g0=all_results['primary']['gate'], with_e05_g0=all_results['with_e05']['gate'], comparisons={})
    for name, fit in fits_by_tag['primary'].items():
        other = fits_by_tag['with_e05'].get(name)
        if fit['converged'] and other and other['converged']:
            a,d=M.item_params(fit); aa,dd=M.item_params(other)
            sensitivity['comparisons'][name] = dict(mean_abs_delta_a=np.abs(aa-a).mean(), max_abs_delta_a=np.abs(aa-a).max(),
                mean_abs_delta_d=np.abs(dd-d).mean(), max_abs_delta_d=np.abs(dd-d).max(),
                mean_abs_delta_p_active=np.abs(other['p_active']-fit['p_active']).mean(),
                theta_delta=other['theta0']-fit['theta0'])
    write_json(args.out / 'e05_sensitivity.json', sensitivity)
    selected = all_results['primary']['selected_model']
    selected_fit = fits_by_tag['primary'].get(selected)
    result = dict(status='complete: strict analysis' if args.phase == 'strict' else 'complete: Phase 0b analysis', trainer_status='FAILED; unchanged', G0=all_results['primary']['gate'],
                   inputs=data['identity'], e05_policy=sensitivity['selection_rule'])
    if args.phase in ('smooth', 'all'):
        # The selected strict prior also regularizes descriptive graded/two-skill fits; no post hoc grid search.
        if selected:
            smooth, dim = smooth_analysis(data, selected_fit, priors_by_tag['primary'][selected], args.repo, args.out)
            result.update(smooth_status=smooth['status'], dimensionality_status=dim['status'])
        else:
            result.update(smooth_status='unavailable: no selected converged strict model', dimensionality_status='unavailable: no selected prior')
    freeze_dir = args.freeze_dir or args.out / 'forecasts'
    result['freeze'] = freeze_parameters(data, selected_fit, all_results['primary'], args.out, freeze_dir)
    write_json(args.out / 'analysis_e20.json', result)
    stamp(args.out, 'complete', **result)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        if '--out' in sys.argv:
            failure_dir = Path(sys.argv[sys.argv.index('--out')+1])
            write_json(failure_dir / 'failure.json', dict(status='BLOCKED', error_type=type(exc).__name__, error=str(exc), trainer_status='FAILED; unchanged'))
        print(f'BLOCKED: {type(exc).__name__}: {exc}', file=sys.stderr, flush=True)
        raise
