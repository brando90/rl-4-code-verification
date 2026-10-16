"""Persistently run the two priority sizes and all eight validation rungs with bounded jobs."""
from __future__ import annotations
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from recovery_watch import identity
from job_process import AdoptedProcess

HERE = Path(__file__).resolve().parent
ROOT = Path('/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3')
NEMO_PY = '/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
PY = '/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/.venv/bin/python'


def main(phase='a'):
    lock = (ROOT / f'phase_{phase}.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert json.loads((HERE / 'results/dry_run_v3.json').read_text())['status'] == 'PASS'
    manifest = json.loads((HERE / 'results/ladder_manifest_v3.json').read_text())
    sizes = ('1.7B', '4B') if phase == 'a' else ('8B', '14B')
    training = [('4b', 2), ('1p7b', 1)] if phase == 'a' else [('8b', 4), ('14b', 8)]
    systems = [s for s in manifest['systems'] if s['size'] in sizes]
    state_path = ROOT / f'phase_{phase}_state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {'jobs': {}}
    unresolved = [k for k, v in state['jobs'].items()
                  if v.get('status') == 'RUNNING' and not v.get('identity')]
    if unresolved:
        raise RuntimeError(f'Reconcile existing child identities before restarting: {unresolved}')
    running = {}
    logs = ROOT / f'phase_{phase}_logs'; logs.mkdir(exist_ok=True)
    task_ids = manifest['task_ids'] if 'task_ids' in manifest else [
        line.strip() for line in (HERE.parent / 'expt_v1/results/split/vbv1_validation_task_ids.txt').read_text().splitlines()
        if line.strip() and not line.startswith('#')]
    for key, job in state['jobs'].items():
        if job.get('status') == 'RUNNING':
            job['key'] = key
            running[key] = (AdoptedProcess(job, ROOT, task_ids), None)
            print('adopted', key, job['identity'], flush=True)

    def save():
        state.update(pid=os.getpid(), identity=identity(os.getpid()), updated_unix=time.time())
        temp = state_path.with_suffix('.tmp')
        temp.write_text(json.dumps(state, indent=2) + '\n'); temp.replace(state_path)

    def launch(key, command, n=0):
        previous = state['jobs'].get(key, {})
        if key in running or previous.get('status') in ('DONE', 'FAILED'):
            return
        if time.time() < previous.get('retry_after', 0):
            return
        if n:
            command = [PY, str(HERE / 'run_with_devices.py'), '--n', str(n), '--name', key, '--', *command]
        stream = (logs / f'{key}.log').open('a')
        attempt = previous.get('attempt', 0) + 1
        receipt = logs / f'{key}.attempt_{attempt}.exit.json'
        process = subprocess.Popen([PY, str(HERE / 'job_process.py'), '--receipt', str(receipt), '--', *command],
                                   stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        running[key] = (process, stream)
        state['jobs'][key] = {'status': 'RUNNING', 'pid': process.pid, 'identity': identity(process.pid),
                              'key': key, 'command': command, 'exit_receipt': str(receipt),
                              'started_unix': time.time(), 'attempt': attempt}
        print('started', key, process.pid, flush=True); save()

    while True:
        if phase == 'b' and json.loads((ROOT / 'phase_a_state.json').read_text()).get('status') != 'DONE':
            state['status'] = 'WAITING_PHASE_A'; save(); time.sleep(60); continue
        changed = False
        for key, (process, stream) in list(running.items()):
            code = process.poll()
            if code is None:
                continue
            if stream is not None:
                stream.close()
            del running[key]
            job = state['jobs'][key]
            job.update(exit_code=code, ended_unix=time.time())
            if code == 3:
                job.update(status='WAITING_DEVICES', retry_after=time.time() + 60)
            elif code == 0:
                job['status'] = 'DONE'; changed = True
            else:
                job['status'] = 'FAILED'; changed = True
            print('finished', key, job['status'], code, flush=True); save()
        for short, n in training:
            for condition in ('E', 'R'):
                key = f'train_{condition}_{short}'
                if condition == 'R' and state['jobs'].get(f'verify_E_{short}', {}).get('status') != 'DONE':
                    continue
                route_path = ROOT / 'training_routes.json'
                routes = json.loads(route_path.read_text()) if route_path.exists() else {}
                if short == '14b' or routes.get(key) == 'remote':
                    launch(key, [PY, str(HERE / 'remote_training.py'), condition, '--size', short])
                else:
                    launch(key, ['bash', str(HERE / 'train_continuation.sh'), condition, short, '{gpus}'], n)
                if state['jobs'].get(key, {}).get('status') == 'DONE':
                    launch(f'verify_{condition}_{short}', [NEMO_PY, str(HERE / 'verify_training.py'), condition, short])
        # Exported half-budget rungs can generate while the second segment trains.
        for s in systems:
            label = s['label']
            if not (Path(s['hf_path']) / 'SHA256SUMS').exists():
                continue
            args = ['bash', str(HERE / 'run_validation.sh'), 'validation', label, s['hf_path'], 'local']
            generation_devices = 1 if phase == 'a' else 4
            route_path = ROOT / 'generation_routes.json'
            routes = json.loads(route_path.read_text()) if route_path.exists() else {}
            if routes.get('gen_' + label) == 'remote':
                launch('gen_' + label, [PY, str(HERE / 'remote_generation.py'), label])
            else:
                launch('gen_' + label, args + ['{gpus}', str(generation_devices), 'generation'], generation_devices)
            if state['jobs'].get('gen_' + label, {}).get('status') == 'DONE':
                # Eight scorer processes per rung; at most two simultaneous scoring/diagnostic rungs.
                active_scores = sum(k.startswith(('score_', 'namespace_')) for k in running)
                if active_scores < 2:
                    launch('score_' + label, args + ['none', '1', 'score'])
        if changed and any(k.startswith('score_') and v['status'] == 'DONE' for k, v in state['jobs'].items()):
            result = subprocess.run([PY, str(HERE / 'analyze_validation.py')], capture_output=True, text=True)
            (logs / 'analysis.log').write_text(result.stdout + result.stderr)
            if result.returncode:
                state['analysis_error'] = result.returncode
                save()
            else:
                state.pop('analysis_error', None)
        for system in systems:
            label = system['label']
            if (HERE / f'results/ladder/{label}_validation_cells.csv').exists():
                active_scores = sum(k.startswith(('score_', 'namespace_')) for k in running)
                if active_scores < 2:
                    launch('namespace_' + label, [PY, str(HERE / 'namespace_diagnostic.py'), label])
        complete = (all(state['jobs'].get('score_' + s['label'], {}).get('status') == 'DONE' for s in systems)
                    and all(state['jobs'].get('namespace_' + s['label'], {}).get('status') == 'DONE' for s in systems)
                    and all(state['jobs'].get(f'verify_{c}_{s}', {}).get('status') == 'DONE' for c in ('E', 'R') for s, _ in training))
        if complete and not state.get('analysis_error'):
            state['status'] = 'DONE'; save(); print(f'Phase {phase.upper()} complete', flush=True); return 0
        failures = [k for k, v in state['jobs'].items() if v['status'] == 'FAILED']
        state['status'] = 'NEEDS_RECOVERY' if failures or state.get('analysis_error') else 'RUNNING'
        state['failed_jobs'] = failures
        save()
        # Failed scientific jobs are preserved, never silently replayed. The owner repairs infrastructure.
        if failures and not running:
            return 1
        time.sleep(20)


if __name__ == '__main__':
    raise SystemExit(main())
