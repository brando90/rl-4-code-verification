"""Evaluate the complete pilot validation split using the inherited sampler and local strict oracle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from technical import ROOT, V3, SOURCE, execute
from cohort import digest
from training_checkpoint import write_new


def validation_paths():
    split = V3.parents[1] / '08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split'
    allow = split / 'vbv1_validation_task_ids.txt'
    if digest(allow) != '666d6d6b31cb3f736d8ca0eee625ff5ad5ea31efa7e0ce3a10c350091848c84d':
        raise ValueError('D-013 validation membership changed')
    if digest(split / 'vbv1_split_manifest.csv') != '157ce781ed9e4ac93a1a1fe0c49f2ee2ae907be1260402485c8f6fa3d06e0e24':
        raise ValueError('D-013 task groups changed')
    return {'allowlist': allow, 'groups': split / 'vbv1_split_manifest.csv',
            'pack': Path('/lfs/skampere1/0/brando9/rl4cv_e08/pack_views/validation')}


def identities(task_ids, split, *, arm, run_seed, boundary):
    if (split != 'validation' or len(task_ids) != 135 or len(set(task_ids)) != 135
            or arm not in ('A', 'B', 'P') or run_seed not in (1301, 1302)
            or boundary not in (0, 30, 60) or boundary == 60 and arm != 'B'):
        raise ValueError('complete declared pilot validation population required')
    return [{'cell_id': f'v3-A7/pilot/{arm}/{run_seed}/{boundary}/validation/{task}/{sample}',
             'task_id': task, 'sample_idx': sample, 'seed': 91 * 100003 + sample,
             'split': 'validation', 'arm': arm, 'run_seed': run_seed, 'boundary': boundary}
            for task in sorted(task_ids) for sample in range(8)]


def install():
    # Adapt only pilot identity admission; prompt/sampler/generation/scoring stay unchanged.
    import evaluation_generation
    evaluation_generation.identities = identities


def freeze(arm, seed, boundary, model, root):
    from pilot_inputs import PREPARATION
    from rl4cv.veribench.pack import load_pack, read_task_ids
    from transformers import AutoTokenizer
    from evaluation_contract import render
    config = json.loads((PREPARATION / 'configuration_A6_S2_T2_A4_OBSERVATION.json').read_text())
    paths = validation_paths()
    allow = {'path': str(paths['allowlist']), 'sha256': digest(paths['allowlist'])}
    if digest(allow['path']) != allow['sha256']:
        raise ValueError('frozen validation membership changed')
    task_ids = read_task_ids(allow['path'])
    cells = identities(task_ids, 'validation', arm=arm, run_seed=seed, boundary=boundary)
    original = json.loads((SOURCE / 'update/runtime.json').read_text())
    tokenizer = AutoTokenizer.from_pretrained(original['tokenizer'], local_files_only=True)
    tasks = load_pack(paths['pack'], task_ids)
    import csv
    groups = {r['task_id']: r['group_id'] for r in csv.DictReader(paths['groups'].open()) if r['split'] == 'validation'}
    if set(groups) != set(task_ids): raise ValueError('validation task-group inventory changed')
    prompts = {}
    for task in tasks:
        value = render(task.instruction, tokenizer, config['scoring']['veribench'])
        prompts[task.task_id] = {**{k: v for k, v in value.items() if k != 'text'},
                                'group_id': groups[task.task_id],
                                'prompt_text': value['text'],
                                'prompt_token_ids': list(tokenizer.encode(value['text']))}
    if set(prompts) != set(task_ids): raise ValueError('validation prompt inventory changed')
    manifest = {'condition': 'v2-S2', 'provenance': 'v3-A7/pilot', 'purpose': 'validation',
                'arm': arm, 'run_seed': seed, 'boundary': boundary,
                'cells': [{**c, **prompts[c['task_id']]} for c in cells]}
    install()
    from evaluation_generation import validate_manifest
    validate_manifest(manifest, task_ids)
    write_new(root / 'manifest.json', manifest)
    write_new(root / 'freeze.json', {'condition': 'v3-A7', 'model': model,
              'manifest_sha256': digest(root / 'manifest.json'), 'allowlist': allow,
              'model_bindings': [{'path': str(p), 'sha256': digest(p)}
                                 for p in sorted(Path(model).iterdir()) if p.is_file()],
              'held_out_outputs_used_for_training': False})
    return manifest, allow['path']


def summarize(manifest, scores):
    from evaluation_contract import strict_summary
    result = strict_summary(manifest['cells'], scores['rows'])
    result.update(condition='v3-A7', metric='validation pass@1',
                  official_SCSC=None, official_SCSC_status='UNMEASURED_COVERAGE_JUDGE_UNAVAILABLE',
                  api_spend_usd=0, p_value=None, imputed=False)
    if 'official_SCSC_summary' in scores:
        composite = scores['official_SCSC_summary']
        result.update(official_SCSC=composite['mean'], official_SCSC_bounds=composite['mean_bounds'],
                      official_SCSC_evidence=composite,
                      official_SCSC_status='DETERMINED_FROM_LOCAL_FACTORS' if composite['mean'] is not None else 'PARTIAL_COVERAGE_UNAVAILABLE')
    # Each frozen task group, with all responses, is one resampling unit. This interval
    # describes task variability for this fixed trained seed, not seed uncertainty.
    if result['missing'] == 0:
        import numpy as np
        task_groups = {c['task_id']: c['group_id'] for c in manifest['cells']}
        groups = sorted(set(task_groups.values()))
        sums = np.array([sum(r['strict'] for r in scores['rows'] if task_groups[r['task_id']] == g) for g in groups])
        counts = np.array([sum(task_groups[r['task_id']] == g for r in scores['rows']) for g in groups])
        indexes = np.random.default_rng(1301).integers(len(groups), size=(10000, len(groups)))
        draws = sums[indexes].sum(axis=1) / counts[indexes].sum(axis=1)
        result['task_bootstrap_95_interval'] = np.quantile(draws, [.025, .975]).tolist()
        result['resampling_groups'] = len(groups)
    else:
        result['task_bootstrap_95_interval'] = None
    result['uncertainty'] = '10,000 frozen-task-group bootstrap replicates, fixed trained seed; no between-seed interval; missing outcomes retain sharp bounds'
    return result


def run(arm, seed, boundary, admission):
    from pilot_run import allocation, check_admission, PILOT
    from pilot_inputs import PREPARATION
    allocation_plan = check_admission(admission)
    if boundary == 0:
        model = json.loads((SOURCE / 'update/runtime.json').read_text())['initial_model']
    else:
        completed = json.loads((PILOT / f'{arm}_{seed}/result_{boundary}.json').read_text())
        if completed['status'] != 'PILOT_UPDATES_COMPLETE': raise ValueError('pilot checkpoint incomplete')
        model = completed['model']
    root = ROOT / 'phase2/validation' / f'{arm}_{seed}_{boundary}'
    root.mkdir(parents=True, exist_ok=False)
    manifest, allowlist = freeze(arm, seed, boundary, model, root)
    refs = {}
    for start in range(0, 1080, 256):
        check_admission(admission)
        indexes = list(range(start, min(1080, start + 256)))
        stage = root / f'generate_{start:05d}'
        with allocation(stage, allocation_plan) as lease:
            execute('pilot_evaluation', stage, lease, manifest=str(root / 'manifest.json'),
                    allowlist=allowlist, model=model, max_model_len=32768, indexes=indexes)
        for i in indexes:
            path = stage / f'output/{i:05d}.generation.json'
            refs[manifest['cells'][i]['cell_id']] = {'path': str(path), 'sha256': digest(path)}
    config = json.loads((PREPARATION / 'configuration_A6_S2_T2_A4_OBSERVATION.json').read_text())['scoring']
    scoring = {**config, 'root': str(root / 'score'), 'purpose': 'validation', 'split': 'validation',
               'allowlist': allowlist, 'controller_fence': str(PILOT / 'scoring.lock')}
    install()
    from score_evaluation import score_manifest
    scores = score_manifest(manifest, scoring, refs, digest(root / 'manifest.json'))
    from scsc_bounds import attach
    scores = attach(scores, root / 'score')
    result = summarize(manifest, scores)
    result.update(arm=arm, seed=seed, boundary=boundary, model=model,
                  status='LOCAL_VALIDATION_MEASURED' if result['official_SCSC'] is not None else 'LOCAL_STRICT_MEASURED_OFFICIAL_SCSC_PENDING')
    write_new(root / 'result.json', result)
    public = V3 / 'results/validation'; public.mkdir(parents=True, exist_ok=True)
    write_new(public / f'{arm}_{seed}_{boundary}.json', {'summary': result, 'scores': scores['rows']})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm', choices=['A', 'B', 'P'], required=True)
    parser.add_argument('--seed', type=int, choices=[1301, 1302], required=True)
    parser.add_argument('--boundary', type=int, choices=[0, 30, 60], required=True)
    parser.add_argument('--admission', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.arm, args.seed, args.boundary, args.admission), sort_keys=True))
