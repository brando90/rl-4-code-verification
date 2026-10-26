"""Execute one admitted paired local GRPO pilot with complete groups, bounded stages and retained receipts."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from technical import ROOT, V3, SOURCE, execute
from cohort import digest
from pilot_inputs import load_inputs, prefix, PREPARATION
from training_checkpoint import write_new, export, verify_files
from rollout_groups import assemble
from score_training import score_batch
from gates import single_rank_gradient

PILOT = ROOT / 'phase2/pilot'


@contextmanager
def allocation(stage_root, admission):
    """Claim only an idle authorized GPU; no process from another owner is signalled."""
    deadline = time.monotonic() + 7 * 86400
    while True:
        query = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used',
                                         '--format=csv,noheader,nounits'], text=True)
        devices = {int(parts[0]): (parts[1].strip(), int(parts[2]))
                   for line in query.splitlines() if (parts := line.split(','))}
        for index in (0, 5, 7):
            if devices[index][1] > 100: continue
            lock = (ROOT / f'gpu_{index}.lock').open('a')
            try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                lock.close()
                continue
            identity = f'e13v3-pilot-{os.getpid()}-{time.time_ns()}'
            lease = stage_root.with_name(stage_root.name + '_lease.json')
            started = time.time()
            try:
                with (ROOT / 'allocation_budget.lock').open('a') as budget_lock:
                    fcntl.flock(budget_lock, fcntl.LOCK_EX)
                    charged = 0.
                    leases = list((ROOT / 'phase2/pilot').glob('*/*/*_lease.json'))
                    leases += list((ROOT / 'phase2/validation').glob('*/*_lease.json'))
                    for other in leases:
                        end = other.with_name(other.stem + '_end.json')
                        charged += json.loads(end.read_text())['device_hours'] if end.exists() else (4 + 120 / 3600)
                    if charged + 4 + 120 / 3600 > admission['device_hour_budget']:
                        raise RuntimeError('cumulative used plus outstanding reserved device hours exhaust pilot allocation')
                    write_new(lease, {'owner': 'e13v3', 'id': identity, 'status': 'ACTIVE', 'index': index,
                                     'uuid': devices[index][0], 'started_unix': started,
                                     'expires_unix': started + 4 * 3600 + 120})
            except BaseException:
                fcntl.flock(lock, fcntl.LOCK_UN); lock.close()
                raise
            os.environ.update(CUDA_VISIBLE_DEVICES=str(index), CUDA_DEVICE_ORDER='PCI_BUS_ID', E13_EXECUTION_ID=identity)
            try:
                yield lease
            finally:
                write_new(lease.with_name(lease.stem + '_end.json'), {'id': identity,
                    'ended_unix': time.time(), 'device_hours': (time.time() - started) / 3600,
                    'gpu_census': subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                                                          '--format=csv,noheader,nounits'], text=True)})
                fcntl.flock(lock, fcntl.LOCK_UN)
                lock.close()
                os.environ['CUDA_VISIBLE_DEVICES'] = ''
            return
        if time.monotonic() >= deadline: raise TimeoutError('no authorized idle GPU within seven days')
        time.sleep(30)


def check_admission(path):
    admission = json.loads(path.read_text())
    if (admission['status'] != 'ADMITTED' or admission['condition'] != 'v3-A7'
            or admission['api_spend_usd'] != 0 or admission['arms'] != ['B', 'A', 'P']
            or admission['seeds'] != [1301, 1302]):
        raise ValueError('complete offline paired pilot admission required')
    for gate in ('T2', 'T3', 'T4'):
        ref = admission['gates'][gate]
        if digest(ref['path']) != ref['sha256']:
            raise ValueError('technical gate evidence changed')
        result = json.loads(Path(ref['path']).read_text())
        if result['condition'] != 'v3-A7' or result['status'] != 'PASS':
            raise ValueError('pilot requires all v3 technical gates to pass')
    if admission['projected_device_hours'] > admission['device_hour_budget']:
        raise ValueError('pilot resource projection exceeds allocation')
    for binding in admission['bindings']:
        if digest(binding['path']) != binding['sha256']:
            raise ValueError('pilot source changed after admission')
    return admission


def retire_previous(root, completed):
    """Keep latest native before/after and export; archive older metadata before retiring only v3 tensors."""
    if completed < 2: return
    previous = root / f'update_{completed-1:05d}'
    if not (previous / 'summary.json').is_file(): raise ValueError('previous opportunity incomplete')
    targets = [(previous / 'update/output/before', 'receipt.json'),
               (previous / 'update/output/after', 'receipt.json'),
               (previous / 'export', 'export_receipt.json')]
    for directory, receipt_name in targets:
        if not directory.exists(): continue
        if directory.is_symlink() or root.resolve() not in directory.resolve().parents:
            raise ValueError('tensor retirement escaped owned pilot run')
        receipt = json.loads((directory / receipt_name).read_text())
        verify_files(directory, receipt['bindings'])
        metadata = previous / ('retired_' + directory.parent.name + '_' + directory.name + '.json')
        write_new(metadata, {'receipt': receipt, 'receipt_sha256': digest(directory / receipt_name),
                             'replaced_by_completed_update': completed, 'removed_path': str(directory)})
        shutil.rmtree(directory)


def run(arm, seed, admission_path, horizon=30):
    admission = check_admission(admission_path)
    if arm not in admission['arms'] or seed not in admission['seeds'] or horizon not in (30, 60):
        raise ValueError('undeclared paired run')
    if horizon == 60:
        extension = json.loads((PILOT / 'B_1301/T5_30.json').read_text())
        if arm != 'B' or extension['status'] != 'EXTEND_TO_60':
            raise ValueError('B extension requires the frozen 30-step gate result')
    root = PILOT / f'{arm}_{seed}'
    root.mkdir(parents=True, exist_ok=True)
    fence = (root / 'controller.lock').open('a')
    fcntl.flock(fence, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (root / f'result_{horizon}.json').exists():
        return json.loads((root / f'result_{horizon}.json').read_text())
    templates, placebo = load_inputs()
    original = json.loads((SOURCE / 'update/runtime.json').read_text())
    model = original['initial_model']; checkpoint = None
    summaries = []
    for update in range(1, horizon + 1):
        check_admission(admission_path)
        work = root / f'update_{update:05d}'
        if (work / 'summary.json').exists():
            summary = json.loads((work / 'summary.json').read_text())
            if summary['admission_sha256'] != digest(admission_path): raise ValueError('pilot admission changed')
            summaries.append(summary); model = summary['model']; checkpoint = summary['checkpoint']
            continue
        if work.exists(): raise RuntimeError('partial opportunity needs diagnosis; no automatic resampling or repeat update')
        if shutil.disk_usage(ROOT).free < 200 * 1024**3:
            raise RuntimeError('fewer than 200 GiB remain for the next complete checkpoint transition')
        work.mkdir()
        plans, cells = prefix(arm, seed, update, templates, placebo)
        write_new(work / 'plans.json', plans); write_new(work / 'cells.json', cells)
        provenance = {'condition': 'v3-A7', 'phase': 'pilot', 'arm': arm, 'run_seed': seed,
                      'update': update, 'admission_sha256': digest(admission_path)}
        common = dict(run_seed=seed, provenance=provenance, cells_path=str(work / 'cells.json'), model=model)
        with allocation(work / 'generate', admission) as lease:
            execute('generate', work / 'generate', lease, **common)
        generated = work / 'generate/output'
        rows = [json.loads((generated / f'{i:05d}.generation.json').read_text()) for i in range(256)]
        config = json.loads((PREPARATION / 'configuration_A6_S2_T2_A4_OBSERVATION.json').read_text())['scoring']
        scoring = {**config, 'root': str(work / 'score/cells'), 'generation_root': str(generated),
                   'controller_fence': str(PILOT / 'scoring.lock')}
        scores = score_batch(cells, scoring,
            {str(generated / f'{i:05d}.generation.json'): digest(generated / f'{i:05d}.generation.json') for i in range(256)},
            digest(admission_path))
        if any(r.get('cleanup_verified') is not True for r in scores['rows']):
            raise RuntimeError('scorer cleanup unresolved')
        groups = assemble(cells, rows, scores['rows'], train_ids=templates, plans=plans)
        if arm == 'B':
            table = {r['cell_id']: r for r in scores['rows']}
            for group in groups:
                for row in group['rows']:
                    score = table[row['cell_id']]
                    expected = score['factored_reward'] if score['status'] == 'measured' else None
                    if row['reward'] != expected: raise ValueError('B reward differs from frozen factored score')
        write_new(work / 'score/groups.json', groups)
        values = [r['reward'] for g in groups for r in g['rows']]
        if all(v is None for v in values):
            raise RuntimeError('all rewards missing; opportunity retained, no fabricated optimizer update')
        kwargs = {**common, 'groups_path': str(work / 'score/groups.json')}
        if checkpoint: kwargs['checkpoint'] = checkpoint
        with allocation(work / 'update', admission) as lease:
            execute('update', work / 'update', lease, **kwargs)
        state = json.loads((work / 'update/output/result.json').read_text())
        checkpoint = str(work / 'update/output/after')
        export(checkpoint, work / 'export', model_config=original['initial_model'], tokenizer=original['tokenizer'])
        model = str(work / 'export')
        complete = [g for g in groups if all(r['reward'] is not None for r in g['rows'])]
        active = sum(len({r['reward'] for r in g['rows']}) > 1 for g in complete)
        measured = [r for r in scores['rows'] if r['status'] == 'measured']
        summary = {**provenance, 'status': 'ACCOUNTED', 'seed': seed, 'split': 'train', 'declared': 256, 'measured': len(measured),
                   'rewards': values, 'reward_mean_observed': sum(v for v in values if v is not None) / sum(v is not None for v in values),
                   'active_groups': active, 'usable_groups': len(complete), 'declared_groups': 32,
                   'active_group_fraction': active / len(complete) if complete else None,
                   'grad_norm': single_rank_gradient(state['metrics']['grad_norm']),
                   'nonzero_advantage_slots': state['counts']['nonzero_advantage_slots'],
                   'loss': state['metrics']['loss'],
                   'strict_successes': sum(r['strict'] for r in measured),
                   'generated_tokens': sum(len(r['output_token_ids']) for r in rows),
                   'parameter_change': state['before_parameters'] != state['after_parameters'],
                   'model': model, 'checkpoint': checkpoint, 'api_spend_usd': 0,
                   'update_result_sha256': digest(work / 'update/output/result.json')}
        write_new(work / 'summary.json', summary); summaries.append(summary)
        public = V3 / 'results/pilot' / f'{arm}_{seed}'; public.mkdir(parents=True, exist_ok=True)
        write_new(public / f'update_{update:05d}.json', {'summary': summary, 'scores': scores['rows']})
        retire_previous(root, update)
    if arm == 'B' and seed == 1301:
        from a6_t5_measurement import evaluate
        result = evaluate(summaries, horizon=horizon)
        result['condition'] = 'v3-A7'
        write_new(root / f'T5_{horizon}.json', result)
    result = {'condition': 'v3-A7', 'status': 'PILOT_UPDATES_COMPLETE', 'arm': arm, 'seed': seed,
              'completed_updates': horizon, 'model': model, 'checkpoint': checkpoint,
              'validation_status': 'PENDING', 'api_spend_usd': 0}
    write_new(root / f'result_{horizon}.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm', required=True, choices=['A', 'B', 'P'])
    parser.add_argument('--seed', required=True, type=int, choices=[1301, 1302])
    parser.add_argument('--admission', required=True, type=Path)
    parser.add_argument('--horizon', type=int, choices=[30, 60], default=30)
    args = parser.parse_args()
    print(json.dumps(run(args.arm, args.seed, args.admission, args.horizon), sort_keys=True))
