"""Execute a single reserved learning stage under its numeric device lease and immutable published admission."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'phase1'))
from device_binding import launch_environment
from lp1 import cleanup
from anchor_lease import release
from training_checkpoint import digest, write_new
from learning_ledger import verify_learning


def authorize(plan):
    run_plan = plan['run']; lp, execution, science = verify_learning(run_plan)
    phase = run_plan['phase']; expected_phase = 'v2-S2-learning-pilot' if phase == 'pilot' else 'v2-S2-main'
    bound = {r['path']: r['sha256'] for r in execution['bindings']}
    for path in (Path(__file__).resolve(), HERE/'learning_runtime.py', HERE.parent/'phase1/device_binding.py',
                 HERE.parent/'phase1/lp1.py', HERE.parent/'phase1/anchor_lease.py'):
        if bound.get(str(path)) != digest(path): raise ValueError('learning launcher dependency unbound')
    stage = plan['stage']; config = json.loads(Path(plan['config']).read_text())
    if stage not in ('preflight', 'generate', 'update', 'export') or config['stage'] != stage:
        raise ValueError('unregistered device learning stage')
    for key in ('arm', 'run_seed'):
        if config[key] != run_plan[key]: raise ValueError('learning runtime run identity changed')
    if config['learning_phase'] != phase or config['condition'] != 'v2-S2': raise ValueError('learning runtime condition changed')
    run_root = Path(execution['configuration']['ledger'])/phase/run_plan['arm']/str(run_plan['run_seed'])
    admission = json.loads((run_root/'admission.json').read_text())
    if (admission.get('status') != 'ADMITTED' or admission.get('execution_lock_sha256') != run_plan['execution_lock']['sha256']
            or any(admission.get(k) != run_plan[k] for k in ('phase','arm','run_seed'))):
        raise ValueError('learning run lacks its immutable admission')
    if (run_root/'terminal.json').exists(): raise ValueError('learning run already terminal')
    expected = run_root/f"update_{config['update']:05d}"/(stage+'.json')
    reservation = Path(plan['reservation'])
    if reservation.resolve() != expected.resolve(): raise ValueError('learning reservation moved outside its ledger')
    record = json.loads(reservation.read_text())
    if (record['execution_sha256'] != run_plan['execution_lock']['sha256'] or record['stage'] != stage
            or record['update'] != config['update']
            or record['inputs']['configuration_sha256'] != digest(plan['config'])):
        raise ValueError('learning stage differs from its exclusive reservation')
    lease = json.loads(Path(config['lease_path']).read_text())
    canonical = json.loads((Path(plan['lease_root'])/(lease['id']+'.json')).read_text())
    if (lease != canonical or lease['phase'] != expected_phase or lease['owner'] != 'e13v2'
            or lease['status'] != 'ACTIVE' or lease['id'] != config['lease_id']
            or lease['host'] != socket.gethostname().split('.')[0]):
        raise ValueError('learning device lease is not the canonical local allocation')
    maximum = plan['maximum_seconds']
    if not 90 < maximum <= lease['expires_unix']-lease['started_unix']:
        raise ValueError('learning stage exceeds its leased duration')
    if record['inputs']['lease_id'] != lease['id'] or record['inputs']['maximum_seconds'] != maximum:
        raise ValueError('learning stage resource reservation changed')
    return config, lease, record


def launch(plan):
    config, lease, reservation = authorize(plan)
    root = Path(plan['dispatch_root']); root.mkdir(parents=True, exist_ok=False)
    result = {'condition': 'v2-S2', 'phase': plan['run']['phase'], 'arm': plan['run']['arm'],
              'run_seed': plan['run']['run_seed'], 'update': config['update'], 'stage': plan['stage'],
              'lease_id': lease['id'], 'automatic_retry': False, 'status': 'INCOMPLETE_INFRA'}
    try:
        env = launch_environment(lease, plan['run']['phase'], {**os.environ, **plan['environment']})
        now = time.time(); remaining = min(now+plan['maximum_seconds'], lease['expires_unix'])-now-90
        if remaining <= 0: raise TimeoutError('learning lease expired before dispatch')
        write_new(root/'launch.json', {**result, 'started_unix': now, 'maximum_seconds': plan['maximum_seconds'],
            'visible_index': env['CUDA_VISIBLE_DEVICES'], 'configuration_sha256': digest(plan['config']),
            'reservation_sha256': digest(plan['reservation']), 'pid': os.getpid(),
            'start_ticks': Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
        with (root/'execution.log').open('x') as log:
            child = subprocess.Popen([config['python'], str(HERE/'learning_runtime.py'), '--config', plan['config'],
                '--stage', plan['stage']], env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            write_new(root/'process.json', {'pid': child.pid, 'marker': lease['id'],
                'start_ticks': Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19],
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
            result['worker_exit_code'] = child.wait(timeout=remaining)
        if result['worker_exit_code']: raise RuntimeError('learning runtime exited nonzero; retained stage is not retried')
        result['status'] = 'RUNTIME_EXITED_ZERO'
    except BaseException as exc:
        result.update(error_type=type(exc).__name__, error=str(exc))
    finally:
        cleaned = cleanup(lease['id']); write_new(root/'cleanup.json', cleaned)
        released = release(plan['lease_root'], lease['id'], cleanup_verified=cleaned['verified'])
        result.update(cleanup_verified=cleaned['verified'], released=released, ended_unix=time.time())
        if not cleaned['verified']: result['status'] = 'CLEANUP_REQUIRED'
        write_new(root/'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    result = launch(json.loads(args.plan.read_text()))
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result['status'] == 'RUNTIME_EXITED_ZERO' else 1)
