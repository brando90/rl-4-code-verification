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
BIN = Path('/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2/bin')
WRAPPER = '''#!/usr/bin/env python3
"""Report a GPU as occupied when any compute process is already on it."""
import os
import subprocess
import sys

REAL = "/usr/bin/nvidia-smi"
args = sys.argv[1:]
query = next((arg for arg in args if arg.startswith("--query-gpu=")), "")
if "memory.used" in query:
    memory = subprocess.check_output(
        [REAL, "--query-gpu=index,uuid,memory.used", "--format=csv,noheader,nounits"], text=True)
    apps = subprocess.check_output(
        [REAL, "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"], text=True)
    busy = set()
    for line in apps.splitlines():
        if not line.strip() or "," not in line:
            continue
        busy.add(line.split(",", 1)[0].strip())
    rows = []
    for line in memory.splitlines():
        if not line.strip():
            continue
        index, uuid, used = [part.strip() for part in line.split(",")]
        if uuid in busy:
            used = str(max(int(used), 101))
        rows.append(f"{index}, {uuid}, {used}")
    print("\\n".join(rows))
else:
    os.execv(REAL, [REAL, *args])
'''


def log(message):
    line = time.strftime('%m-%d-%Y %H:%M:%S %Z') + ' ' + message
    print(line, flush=True)
    with LOG.open('a') as stream:
        stream.write(line + '\n')


def generations(work):
    output = work / 'generate/output'
    return list(output.glob('*.generation.json')) if output.exists() else []


def unique_dir(path):
    dest = path
    number = 2
    while dest.exists():
        dest = path.with_name(path.name + f'_{number}')
        number += 1
    return dest


def archive_without_generations(arm, seed, update):
    work = PILOT / f'{arm}_{seed}' / f'update_{update:05d}'
    if not work.exists() or (work / 'summary.json').exists():
        return
    if generations(work):
        raise RuntimeError(f'{arm}_{seed} update {update} has generations; not discarding them')
    dest = unique_dir(work.with_name(work.name + '_infrastructure_10-19-2026'))
    work.rename(dest)
    log(f'archived {arm}_{seed} update {update} with zero generations')


def optimizer_complete(work):
    """A result alone is not a resumable optimizer state (UNMEASURED has no after/)."""
    return ((work / 'update/output/result.json').is_file()
            and (work / 'update/output/after/receipt.json').is_file())


def account(arm, seed, update, admission_path):
    """Write the normal summary for an update whose optimizer result is already on disk."""
    root = PILOT / f'{arm}_{seed}'
    work = root / f'update_{update:05d}'
    if (work / 'summary.json').exists():
        return
    result_path = work / 'update/output/result.json'
    if not optimizer_complete(work):
        raise RuntimeError(f'{arm}_{seed} update {update} has no complete optimizer checkpoint; '
                           'result.json alone cannot be accounted')
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


def park_old_lease(work):
    """Keep the failed attempt's device-hour receipt without blocking a new lease file."""
    lease = work / 'update_lease.json'
    if not lease.exists():
        return
    attempt = 1
    while (work / f'update_attempt{attempt}_lease.json').exists():
        attempt += 1
    parked = work / f'update_attempt{attempt}_lease.json'
    end = work / 'update_lease_end.json'
    lease.rename(parked)
    if end.exists():
        end.rename(work / f'update_attempt{attempt}_lease_end.json')
    log(f'parked prior optimizer lease at {parked.name}')


def retry_optimizer(arm, seed, update, admission):
    """Run the optimizer once on generations and scores that already exist."""
    root = PILOT / f'{arm}_{seed}'
    work = root / f'update_{update:05d}'
    if (work / 'summary.json').exists():
        return
    if optimizer_complete(work):
        account(arm, seed, update, ADMISSION)
        return
    if not (work / 'score/groups.json').exists() or len(generations(work)) != 256:
        raise RuntimeError(f'{arm}_{seed} update {update} is not a scored complete generation')
    previous = json.loads((root / f'update_{update-1:05d}/summary.json').read_text())
    if not (Path(previous['checkpoint']) / 'receipt.json').is_file():
        raise RuntimeError('previous completed update has no checkpoint receipt; diagnosis required')
    failed = work / 'update'
    if failed.exists():
        dest = unique_dir(work / 'update_failed_permission_10-19-2026')
        failed.rename(dest)
        log(f'preserved failed optimizer attempt for {arm}_{seed} update {update}')
    if (work / 'export').exists():
        (work / 'export').rename(unique_dir(work / 'export_failed_optimizer'))
    park_old_lease(work)
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
    partials = [path for path in numbered_updates(root) if not (path / 'summary.json').exists()]
    if partials:
        raise RuntimeError(f'{arm}_{seed} still has an unaudited partial: {[p.name for p in partials]}')
    name = f'rl4cv-e13v3-pilot-{arm}-{seed}'
    existing = subprocess.run(['tmux', 'has-session', '-t', name], capture_output=True)
    if existing.returncode == 0:
        log(f'{name} already running')
        return
    command = (f'cd {HERE} && PATH={BIN}:$PATH PYTHONPATH={RL4CV_SRC} HF_HUB_OFFLINE=1 {PYTHON} '
               f'pilot_run.py --arm {arm} --seed {seed} --horizon 30 --admission {ADMISSION}')
    subprocess.run(['tmux', 'new-session', '-d', '-s', name, command], check=True)
    log(f'started {name}')


def install_gpu_filter():
    """Skip a GPU that already has a compute process, without editing the hashed guard."""
    BIN.mkdir(parents=True, exist_ok=True)
    target = BIN / 'nvidia-smi'
    # Live jobs execute this wrapper; never truncate it in place (master fix 10-20-2026).
    if not (target.exists() and target.read_text() == WRAPPER):
        tmp = BIN / f'.nvidia-smi.{os.getpid()}.tmp'
        tmp.write_text(WRAPPER)
        tmp.chmod(0o755)
        os.replace(tmp, target)
    os.environ['PATH'] = f'{BIN}{os.pathsep}{os.environ.get("PATH", "")}'


def numbered_updates(root):
    """Live update directories only. Archived attempts keep a longer suffix."""
    updates = [path for path in root.glob('update_*')
               if path.is_dir() and len(path.name) == 12 and path.name[7:].isdigit()]
    return sorted(updates, key=lambda path: path.name)


def resume_partials():
    """Archive empty failures, account finished optimizer steps, and retry complete generations."""
    ready = []
    retries = []
    for root in sorted(path for path in PILOT.iterdir() if path.is_dir() and '_' in path.name):
        arm, seed_text = root.name.split('_', 1)
        seed = int(seed_text)
        for work in numbered_updates(root):
            if (work / 'summary.json').exists():
                continue
            update = int(work.name.split('_')[1])
            if optimizer_complete(work):
                account(arm, seed, update, ADMISSION)
                continue
            if not generations(work):
                archive_without_generations(arm, seed, update)
                continue
            if len(generations(work)) == 256 and (work / 'score/groups.json').exists():
                retries.append((arm, seed, update))
                continue
            raise RuntimeError(f'{root.name} {work.name} has a partial generation; leaving it untouched')
        if not any(not (path / 'summary.json').exists() for path in numbered_updates(root)):
            ready.append((arm, seed))
    return ready, retries


def spawn_retry(arm, seed, update):
    name = f'rl4cv-e13v3-retry-{arm}-{seed}-u{update}'
    if subprocess.run(['tmux', 'has-session', '-t', name], capture_output=True).returncode == 0:
        log(f'{name} already running')
        return
    command = (f'cd {HERE} && PATH={BIN}:$PATH PYTHONPATH={RL4CV_SRC} HF_HUB_OFFLINE=1 {PYTHON} '
               f'{Path(__file__).resolve()} retry {arm} {seed} {update}')
    subprocess.run(['tmux', 'new-session', '-d', '-s', name, command], check=True)
    log(f'started {name}')


def main(argv):
    os.environ['HF_HUB_OFFLINE'] = '1'
    if argv[:1] == ['retry']:
        arm, seed, update = argv[1], int(argv[2]), int(argv[3])
        install_gpu_filter()
        retry_optimizer(arm, seed, update, check_admission(ADMISSION))
        launch(arm, seed)
        log(f'retry finished for {arm}_{seed} update {update}; provider spend remains $0')
        return
    check_admission(ADMISSION)
    install_gpu_filter()
    ready, retries = resume_partials()
    for arm, seed in ready:
        launch(arm, seed)
    for arm, seed, update in retries:
        spawn_retry(arm, seed, update)
    log('pilot resume launched; provider spend remains $0')


if __name__ == '__main__':
    main(sys.argv[1:])
