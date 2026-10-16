"""Recompile namespace-escaped copies of validation files without changing primary results."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e08')
SCORER = WORK / 'rl-4-code-verification/external/veribench_scorer/scripts/scsc'
LAKE = WORK / 'grading/lean_src'
sys.path[:0] = [str(REPO / 'src'), str(HERE.parent / 'expt_v1/scripts')]
from rl4cv.rewards import ScoredResponse, reward_kernel_binary
from score_teacher_files import vacuity


def helpers():
    path = REPO / 'experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/diagnostics/diagnose_zero_scores.py'
    spec = importlib.util.spec_from_file_location('e01_namespace_helpers', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scorer = module.frozen_scorer(str(SCORER))
    return module, scorer


def check(job):
    diag, scorer = helpers()
    path = Path(job['path'])
    receipt = path.with_suffix('.json')
    if receipt.exists():
        old = json.loads(receipt.read_text())
        assert old['transformed_sha256'] == job['transformed_sha256']
        return old
    result = {**job, 'kernel_binary': None, 'IC_tests': None, 'IC_proofs': None}
    compiled = diag.compile_file(path, str(LAKE), 600)
    result.update(compiles=compiled['success'], compile_timeout=compiled['timeout'], seconds=compiled['seconds'],
                  first_error=compiled['errors'][0]['msg'] if compiled['errors'] else None)
    if not compiled['timeout']:
        if not compiled['success']:
            result.update(kernel_binary=0, IC_tests=0, IC_proofs=0)
        else:
            analysis = scorer.analyze_lean_file(str(path), job['task_id'].split('__')[0])
            analysis.compiles = True
            proof = scorer.ic_pp_for_compiled(str(path), str(LAKE), analysis)
            kernel = analysis.kernel or {}
            nv = vacuity(path.read_text())
            response = ScoredResponse(extracted=True, compiles=analysis.compiles, n_examples=analysis.n_examples,
                                      n_theorems_stated=kernel.get('n_theorems', analysis.n_theorems),
                                      n_theorems_proved=kernel.get('n_honest', 0), vacuous_theorems=nv['n_vacuous'])
            binary = reward_kernel_binary(response)
            if nv['unparseable'] and binary == 1:
                binary = 0
            result.update(kernel_binary=binary, IC_tests=response.ic_tests, IC_proofs=proof,
                          kernel=kernel, nonvacuity=nv, compiles=analysis.compiles)
    receipt.write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label')
    args = parser.parse_args()
    manifest = json.loads((HERE / 'results/ladder_manifest_v3.json').read_text())
    assert args.label in {r['label'] for r in manifest['systems']}
    primary = list(csv.DictReader((HERE / f'results/ladder/{args.label}_validation_cells.csv').open()))
    assert len(primary) == 1080 and all(r['known'] == 'True' for r in primary)
    raw = [json.loads(l) for l in (WORK / f'sft_v3/ladder/validation/raw/gen_{args.label}_g8.jsonl').read_text().splitlines()]
    original_by_id = {(r['task_id'], int(r['sample_idx'])): r for r in primary}
    assert len(raw) == len(original_by_id) == 1080
    assert {(r['task_id'], int(r['sample_idx'])) for r in raw} == set(original_by_id)
    diag, _ = helpers()
    root = WORK / f'sft_v3/namespace_diagnostic/{args.label}'; root.mkdir(parents=True, exist_ok=True)
    jobs = []
    for row in raw:
        original = row.get('lean') or ''
        primary_hash = original_by_id[row['task_id'], int(row['sample_idx'])]['lean_sha256']
        assert not original or hashlib.sha256(original.encode()).hexdigest() == primary_hash
        changed, count = diag.escape_digit_namespaces(original)
        if changed == original:
            continue
        folder = root / row['task_id'] / str(row['sample_idx']); folder.mkdir(parents=True, exist_ok=True)
        path = folder / 'solution.lean'; path.write_text(changed)
        jobs.append({'task_id': row['task_id'], 'sample_idx': int(row['sample_idx']), 'names_escaped': count,
                     'original_sha256': hashlib.sha256(original.encode()).hexdigest(),
                     'transformed_sha256': hashlib.sha256(changed.encode()).hexdigest(), 'path': str(path)})
    with ProcessPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, jobs))
    by_id = {(r['task_id'], r['sample_idx']): r for r in results}
    combined = []
    for row in primary:
        r = by_id.get((row['task_id'], int(row['sample_idx'])))
        original = float(row['kernel_binary'])
        combined.append({'task_id': row['task_id'], 'sample_idx': row['sample_idx'], 'original_kernel_binary': original,
                         'diagnostic_kernel_binary': r['kernel_binary'] if r else original,
                         'changed': r is not None, 'original_sha256': row['lean_sha256'],
                         'transformed_sha256': r['transformed_sha256'] if r else row['lean_sha256']})
    out = HERE / 'results/namespace_diagnostic'; out.mkdir(exist_ok=True)
    with (out / f'{args.label}_cells.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(combined[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(combined)
    summary = {'system': args.label, 'declared_cells': 1080, 'changed_cells': len(results),
               'unknown_cells': sum(r['diagnostic_kernel_binary'] is None for r in combined),
               'original_successes': sum(r['original_kernel_binary'] for r in combined),
               'diagnostic_successes_known': sum(r['diagnostic_kernel_binary'] or 0 for r in combined),
               'scope': 'Diagnostic only; primary scores, gates and selection unchanged; zero model calls', 'changed_receipts': results}
    if not summary['unknown_cells']:
        deltas = np.array([sum(r['diagnostic_kernel_binary'] - r['original_kernel_binary']
                              for r in combined if r['task_id'] == task) / 8 for task in manifest['task_ids']])
        draws = np.random.default_rng(0).integers(0, 135, (10000, 135))
        summary['paired_task_bootstrap_delta'] = {'mean': float(deltas.mean()),
                'ci95': np.quantile(deltas[draws].mean(axis=1), [.025, .975]).tolist(),
                'draws': 10000, 'seed': 0, 'p_value': None, 'unit': 'task with eight attempts together'}
    (out / f'{args.label}.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'changed_receipts'}))


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    main()
