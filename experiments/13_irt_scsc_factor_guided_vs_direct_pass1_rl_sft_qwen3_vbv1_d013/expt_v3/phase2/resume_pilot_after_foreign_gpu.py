#!/usr/bin/env python3
"""Resume the local factored-reward pilot after foreign-GPU failures, without new samples or provider calls.

Completed generations and a finished optimizer step are kept. An update directory with no
generation files is an infrastructure failure and is archived so the same update index can
be attempted once the authorized GPUs are idle.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(HERE))

from pilot_run import (PILOT, PREPARATION, SOURCE, allocation, check_admission, digest,
                       execute, export, load_inputs, retire_previous, score_batch, write_new)
from gates import single_rank_gradient

ADMISSION = Path('/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2/pilot_admission.json')
PYTHON = '/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
RL4CV_SRC = '/lfs/skampere1/0/brando9/rl4cv_e13v2/rl-4-code-verification/src'
LOG = Path('/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2/resume_pilot_after_foreign_gpu.log')


def log(message):
    line = time.strftime('%m-%d-%Y %H:%M:%S %Z') + ' ' + message
    print(line, flush=True)
    with LOG.open('a') as stream:
        stream.write(line + '\n')


def generations(work):
    output = work / 'generate/output'
    return list(output.glob('*.generation.json')) if output.exists() else []


def archive_without_generations(arm, seed, update):
    work = PILOT / f'{arm}_{seed}' / f'update_{update:05d}'
    if not work.exists() or (work / 'summary.json').exists():
        return
    if generations(work):
        raise RuntimeError(f'{arm}_{seed} update {update} has generations; not discarding them')
    dest = work.with_name(work.name + '_infrastructure_10-18-2026')
    if dest.exists():
        raise RuntimeError(f'archive already exists: {dest}')
    work.rename(dest)
    log(f'archived {arm}_{seed} update {update} with zero generations')


def account(arm, seed, update, admission_path):
    """Write the normal summary for an update whose optimizer result is already on disk."""
    root = PILOT / f'{arm}_{seed}'
    work = root / f'update_{update:05d}'
    if (work / 'summary.json').exists():
        return
    result_path = work / 'update/output/result.json'
    if not result_path.exists():
        raise RuntimeError(f'{arm}_{seed} update {update} has no optimizer result')
    if len(generations(work)) != 256:
        raise RuntimeError(f'{arm}_{seed} update {update} does not have 256 generations')
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    original = json.loads((SOURCE / 'update/runtime.json').read_text())
    if not (work / 'export/export_receipt.json').exists():
        export(str(work / 'update/output/after'), work / 'export',
               model_config=original['initial_model'], tokenizer=original['tokenizer'])
        log(f'exported {arm}_{seed} update {update}')
    generated = work / 'generate/output'
    cells = json.loads((work / 'cells.json').read_text())
    rows = [json.loads((generated / f'{i:05d}.generation.json').read_text()) for i in range(256)]
    config = json.loads((PREPARATION / 'configuration_A6_S2_T2_A4_OBSERVATION.json').read_text())['scoring']
    scoring = {**config, 'root': str(work / 'score/cells'), 'generation_root': str(generated),
               'controller_fence': str(PILOT / 'scoring.lock')}
    scores = score_batch(cells, scoring,
        {str(generated / f'{i:05d}.generation.json'): digest(generated / f'{i:05d}.generation.json') for i in range(256)},
        digest(admission_path))
    groups = json.loads((work / 'score/groups.json').read_text())
    state = json.loads(result_path.read_text())
    provenance = {'condition': 'v3-A7', 'phase': 'pilot', 'arm': arm, 'run_seed': seed,
                  'update': update, 'admission_sha256': digest(admission_path)}
    values = [r['reward'] for g in groups for r in g['rows']]
    complete = [g for g in groups if all(r['reward'] is not None for r in g['rows'])]
    active = sum(len({r['reward'] for r in g['rows']}) > 1 for g in complete)
    measured = [r for r in scores['rows'] if r['status'] == 'measured']
    summary = {**provenance, 'status': 'ACCOUNTED', 'seed': seed, 'split': 'train', 'declared': 256,
               'measured': len(measured), 'rewards': values,
               'reward_mean_observed': sum(v for v in values if v is not None) / sum(v is not None for v in values),
               'active_groups': active, 'usable_groups': len(complete), 'declared_groups': 32,
               'active_group_fraction': active / len(complete) if complete else None,
               'grad_norm': single_rank_gradient(state['metrics']['grad_norm']),
               'nonzero_advantage_slots': state['counts']['nonzero_advantage_slots'],
               'loss': state['metrics']['loss'],
               'strict_successes': sum(r['strict'] for r in measured),
               'generated_tokens': sum(len(r['output_token_ids']) for r in rows),
               'parameter_change': state['before_parameters'] != state['after_parameters'],
               'model': str(work / 'export'), 'checkpoint': str(work / 'update/output/after'),
               'api_spend_usd': 0, 'update_result_sha256': digest(result_path)}
    write_new(work / 'summary.json', summary)
    public = HERE.parent / 'results/pilot' / f'{arm}_{seed}'
    public.mkdir(parents=True, exist_ok=True)
    write_new(public / f'update_{update:05d}.json', {'summary': summary, 'scores': scores['rows']})
    retire_previous(root, update)
    log(f'accounted {arm}_{seed} update {update}')


def retry_optimizer(arm, seed, update, admission):
    """Run the optimizer once on generations and scores that already exist."""
    root = PILOT / f'{arm}_{seed}'
    work = root / f'update_{update:05d}'
    if (work / 'summary.json').exists():
        return
    if (work / 'update/output/result.json').exists():
        account(arm, seed, update, ADMISSION)
        return
    if not (work / 'score/groups.json').exists() or len(generations(work)) != 256:
        raise RuntimeError(f'{arm}_{seed} update {update} is not a scored complete generation')
    failed = work / 'update'
    if failed.exists():
        dest = work / 'update_failed_permission_10-18-2026'
        if dest.exists():
            raise RuntimeError(f'failed update archive already exists for {arm}_{seed}')
        failed.rename(dest)
        log(f'preserved failed optimizer attempt for {arm}_{seed} update {update}')
    previous = json.loads((root / f'update_{update-1:05d}/summary.json').read_text())
    provenance = {'condition': 'v3-A7', 'phase': 'pilot', 'arm': arm, 'run_seed': seed,
                  'update': update, 'admission_sha256': digest(ADMISSION)}
    kwargs = dict(run_seed=seed, provenance=provenance, cells_path=str(work / 'cells.json'),
                  model=previous['model'], groups_path=str(work / 'score/groups.json'),
                  checkpoint=previous['checkpoint'])
    log(f'waiting for an idle GPU to optimize {arm}_{seed} update {update}')
    with allocation(work / 'update', admission) as lease:
        execute('update', work / 'update', lease, **kwargs)
    account(arm, seed, update, ADMISSION)


def launch(arm, seed):
    root = PILOT / f'{arm}_{seed}'
    partials = [p for p in root.glob('update_*') if p.is_dir() and p.name[7:12].isdigit()
                and not (p / 'summary.json').exists() and 'infrastructure' not in p.name
                and 'failed' not in p.name]
    if partials:
        raise RuntimeError(f'{arm}_{seed} still has an unaudited partial: {[p.name for p in partials]}')
    name = f'rl4cv-e13v3-pilot-{arm}-{seed}'
    existing = subprocess.run(['tmux', 'has-session', '-t', name], capture_output=True)
    if existing.returncode == 0:
        log(f'{name} already running')
        return
    command = (f'cd {HERE} && PYTHONPATH={RL4CV_SRC} HF_HUB_OFFLINE=1 {PYTHON} '
               f'pilot_run.py --arm {arm} --seed {seed} --horizon 30 --admission {ADMISSION}')
    subprocess.run(['tmux', 'new-session', '-d', '-s', name, command], check=True)
    log(f'started {name}')


def main():
    os.environ['HF_HUB_OFFLINE'] = '1'
    admission = check_admission(ADMISSION)
    for arm, seed in (('A', 1302), ('B', 1302), ('P', 1302)):
        archive_without_generations(arm, seed, 1)
    if not (PILOT / 'A_1301/update_00010/summary.json').exists():
        account('A', 1301, 10, ADMISSION)
    retry_optimizer('B', 1301, 10, admission)
    retry_optimizer('P', 1301, 9, admission)
    for arm, seed in (('B', 1301), ('A', 1301), ('P', 1301), ('B', 1302), ('A', 1302), ('P', 1302)):
        launch(arm, seed)
    log('pilot resume launched; provider spend remains $0')


if __name__ == '__main__':
    main()
