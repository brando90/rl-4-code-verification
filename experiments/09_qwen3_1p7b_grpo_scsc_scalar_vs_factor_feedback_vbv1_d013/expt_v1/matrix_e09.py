"""TLDR: Full-denominator aligned factors/strict target and paired task-bootstrap analysis."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import random
import statistics

SEEDS = (20261008, 20261009)
EVAL_SEED = 20261010
BOOTSTRAP_SEED = 20261011
BOOTSTRAP_DRAWS = 10000
FIELDS = ('task_id', 'split', 'policy', 'arm', 'training_seed', 'checkpoint_sha256',
          'extracted', 'compiles', 'IC_tests', 'IC_proofs', 'FSC', 'S', 'H',
          'kernel_binary', 'truncated', 'generated_tokens', 'judge_ratings', 'cost_usd',
          'status', 'error', 'fsc_status')


def manifest(split_ids, checkpoints=None):
    """IDs alone are sufficient; no held-out task contents/outcomes are opened."""
    checkpoints = checkpoints or {}
    policies = [('baseline', 'baseline', None)] + [(f'{arm}_{seed}', arm, seed)
                for seed in SEEDS for arm in 'ABC']
    rows = []
    assert set(split_ids) == {'validation', 'test'}
    assert len(split_ids['validation']) == 135 and len(split_ids['test']) == 222
    assert len(set(split_ids['validation'] + split_ids['test'])) == 357
    for split, ids in split_ids.items():
        for task_id in ids:
            for policy, arm, seed in policies:
                row = dict.fromkeys(FIELDS)
                row.update(task_id=task_id, split=split, policy=policy, arm=arm, training_seed=seed,
                           checkpoint_sha256=checkpoints.get(policy), status='not_run',
                           error='prerequisite_not_admitted', fsc_status='not_requested')
                rows.append(row)
    assert len(rows) == 2499
    return rows


def reconcile(declared, measured):
    keys = lambda r: (r['split'], r['task_id'], r['policy'])
    by_key = {keys(r): dict(r) for r in declared}
    assert len(by_key) == len(declared)
    seen = set()
    for row in measured:
        key = keys(row)
        if key in seen or key not in by_key:
            raise ValueError('Duplicate or undeclared evaluation cell')
        seen.add(key)
        old = by_key[key]
        if old['checkpoint_sha256'] is None or row['checkpoint_sha256'] != old['checkpoint_sha256']:
            raise ValueError('Endpoint not frozen or measurement checkpoint differs')
        for factor in ('IC_tests', 'IC_proofs', 'FSC', 'S', 'H'):
            val = row.get(factor)
            if val is not None and not 0 <= val <= 1:
                raise ValueError('Factor/target out of range')
        if row.get('H') not in (None, 0, 1):
            raise ValueError('Harsh target is binary')
        if row['status'] == 'measured' and (row.get('S') is None or row.get('H') is None):
            raise ValueError('Missing required outcome cannot be measured')
        by_key[key].update(row)
    return [by_key[keys(r)] for r in declared]


def write_matrix(rows, root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'aligned_task_factors.jsonl').open('w') as out:
        for row in rows:
            out.write(json.dumps(row, sort_keys=False) + '\n')
    with (root / 'aligned_task_factors.csv').open('w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS, extrasaction='ignore', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def bootstrap(values):
    if not values:
        return {'effect': None, 'ci95': [None, None], 'tasks': 0, 'p_val': 'n/a'}
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(values)
    draws = sorted(statistics.fmean(rng.choices(values, k=n)) for _ in range(BOOTSTRAP_DRAWS))
    return {'effect': statistics.fmean(values), 'ci95': [draws[249], draws[9749]],
            'tasks': n, 'draws': BOOTSTRAP_DRAWS, 'bootstrap_seed': BOOTSTRAP_SEED,
            'resampling_unit': 'task', 'p_val': 'n/a'}


def paired(rows, split, left_arm, right_arm):
    panel = {(r['task_id'], r['arm'], r['training_seed']): r for r in rows if r['split'] == split}
    tasks = sorted({key[0] for key in panel})
    per_seed, task_effects = {}, {}
    for seed in SEEDS:
        deltas, lo, hi = {}, [], []
        for task in tasks:
            left = panel[(task, left_arm, seed)]
            right = panel[(task, right_arm, None if right_arm == 'baseline' else seed)]
            a, b = left['H'], right['H']
            if a is not None and b is not None:
                deltas[task] = a - b
            lo.append((0 if a is None else a) - (1 if b is None else b))
            hi.append((1 if a is None else a) - (0 if b is None else b))
        per_seed[str(seed)] = {**bootstrap(list(deltas.values())), 'declared_tasks': len(tasks),
                              'full_denominator_missingness_bounds': [statistics.fmean(lo), statistics.fmean(hi)]}
        task_effects[seed] = deltas
    common = sorted(set.intersection(*(set(v) for v in task_effects.values())))
    pooled = bootstrap([statistics.fmean(task_effects[s][t] for s in SEEDS) for t in common])
    seed_means = [v['effect'] for v in per_seed.values() if v['effect'] is not None]
    return {'comparison': f'{left_arm}-{right_arm}', 'split': split, 'per_seed': per_seed,
            'pooled_paired_task_cohort': pooled, 'declared_training_seeds': 2,
            'measured_seed_comparisons': len(seed_means),
            'seed_spread': max(seed_means) - min(seed_means) if len(seed_means) == 2 else None,
            'limits': 'Two training seeds; task-bootstrap uncertainty does not establish seed-population generalization.'}


def before_after(rows):
    baseline = {(r['split'], r['task_id']): r for r in rows if r['arm'] == 'baseline'}
    result = []
    for row in rows:
        if row['arm'] == 'baseline':
            continue
        before = baseline[(row['split'], row['task_id'])]
        entry = {k: row[k] for k in ('task_id', 'split', 'policy', 'training_seed', 'checkpoint_sha256')}
        for key in ('IC_tests', 'IC_proofs', 'FSC', 'S', 'H', 'kernel_binary', 'compiles', 'truncated'):
            a, b = before[key], row[key]
            entry[key + '_before'], entry[key + '_after'] = a, b
            entry[key + '_delta'] = b - a if a is not None and b is not None else None
        a, b = before['H'], row['H']
        entry['H_transition'] = f'{int(a)}->{int(b)}' if a is not None and b is not None else None
        entry['regression'] = a == 1 and b == 0 if a is not None and b is not None else None
        result.append(entry)
    return result


def summarize(rows):
    comparisons = [paired(rows, split, a, b) for split in ('validation', 'test')
                   for a, b in [('C', 'B'), ('B', 'A'), ('A', 'baseline'), ('B', 'baseline'), ('C', 'baseline')]]
    counts = {}
    for split in ('validation', 'test'):
        selected = [r for r in rows if r['split'] == split]
        counts[split] = {'declared': len(selected), 'measured': sum(r['status'] == 'measured' for r in selected),
                         'missing': sum(r['status'] != 'measured' for r in selected)}
    return {'counts': counts, 'paired_H': comparisons,
            'eval_seed': EVAL_SEED, 'before_after': before_after(rows)}


def main():
    import argparse
    import hashlib
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--reason', default='prerequisite_not_admitted')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    split_root = repo / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split'
    split_files = {s: split_root / f'vbv1_{s}_task_ids.txt' for s in ('validation', 'test')}
    ids = {s: p.read_text().splitlines() for s, p in split_files.items()}
    rows = manifest(ids)
    for row in rows:
        row['error'] = args.reason
    write_matrix(rows, args.out)
    summary = summarize(rows)
    before = summary.pop('before_after')
    with (args.out / 'before_after.jsonl').open('w') as out:
        for row in before:
            out.write(json.dumps(row) + '\n')
    summary['split_id_file_sha256'] = {s: hashlib.sha256(p.read_bytes()).hexdigest() for s, p in split_files.items()}
    summary['source_material_opened'] = 'IDs only; no validation/test prompt, reference or outcome was read'
    summary['endpoint_identities_frozen'] = False
    summary['status'] = args.reason
    (args.out / 'analysis.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    from train_schedule_e09 import schedule, SPLIT
    calibration = []
    for item in schedule(SPLIT.read_text().splitlines(), SEEDS[0], 32):
        for sample in range(8):
            for turn in (1, 2):
                calibration.append({**item, 'sample': sample, 'turn': turn, 'IC_tests': None,
                    'IC_proofs': None, 'FSC': None, 'S': None, 'H': None,
                    'status': 'not_run', 'error': args.reason})
    with (args.out / 'calibration_cells.jsonl').open('w') as out:
        for row in calibration:
            out.write(json.dumps(row) + '\n')
    training = {'trajectories': [{'arm': arm, 'seed': seed, 'horizon_updates': None,
                  'optimizer_updates': 0, 'responses': 0, 'endpoint_sha256': None,
                  'status': 'not_admitted', 'error': args.reason} for seed in SEEDS for arm in 'ABC'],
                'declared_trajectories': 6, 'admitted_trajectories': 0,
                'chosen_horizon': None, 'permitted_horizons': [32, 16, 8],
                'main_response_upper_bound': 12288,
                'note': 'No horizon was admitted; the maximum plan is not a fabricated chosen denominator.'}
    (args.out / 'training_trajectories.json').write_text(json.dumps(training, indent=2) + '\n')
    print(json.dumps(summary['counts']))


if __name__ == '__main__':
    main()
