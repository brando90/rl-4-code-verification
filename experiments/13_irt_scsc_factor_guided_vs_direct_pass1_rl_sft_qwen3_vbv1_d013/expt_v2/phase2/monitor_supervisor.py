"""Run a fixed pilot-monitor snapshot only while its owning learning controller is paused at that checkpoint."""
from __future__ import annotations

import argparse
import fcntl
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
from technical_ledger import published,check_preflight
from technical_runtime import bound


def authorize(plan):
    run=plan['run'];lp,execution,science=verify_learning(run)
    if run['phase']!='pilot' or run['arm'] not in ('B','C') or run['run_seed']!=1301:
        raise ValueError('monitor requires the fixed B/C pilot run')
    scientific={b['path']:b['sha256'] for b in execution['bindings']}
    required=[Path(__file__).resolve(),HERE/'monitor_runtime.py',HERE/'monitor_preparation.py',
        HERE.parent/'phase1/device_binding.py',HERE.parent/'phase1/lp1.py',HERE.parent/'phase1/anchor_lease.py']
    if any(scientific.get(str(p))!=digest(p) for p in required):raise ValueError('monitor launcher unbound before learning')
    snapshot=published(plan['snapshot_lock'],run['repository'])
    if (snapshot.get('gate'),snapshot.get('condition'),snapshot.get('status'))!=('PILOT_MONITOR_SNAPSHOT','v2-S2','FROZEN'):
        raise ValueError('published monitor snapshot freeze required')
    if snapshot['execution_sha256']!=run['execution_lock']['sha256'] or any(snapshot[k]!=run[k] for k in ('arm','run_seed')):
        raise ValueError('snapshot belongs to another pilot')
    if snapshot['update'] not in (0,10,20,30):raise ValueError('undeclared monitor checkpoint')
    inputs={b['path']:b['sha256'] for b in snapshot['bindings']}
    if len(inputs)!=len(snapshot['bindings']):raise ValueError('duplicate snapshot binding')
    if any(digest(p)!=sha for p,sha in inputs.items()):raise ValueError('pre-response snapshot binding changed')
    root=Path(execution['configuration']['ledger'])/'pilot'/run['arm']/str(run['run_seed'])
    admission=json.loads((root/'admission.json').read_text());state=json.loads((root/'state.json').read_text())
    if (admission.get('status')!='ADMITTED' or admission.get('execution_lock_sha256')!=run['execution_lock']['sha256']
            or (root/'terminal.json').exists()):raise ValueError('pilot is not actively admitted')
    if (state['status']!='WAIT_FOR_MONITOR' or state['next_stage']!='monitor'
            or state['completed_updates']!=snapshot['update'] or state['execution_sha256']!=snapshot['execution_sha256']
            or digest(root/'state.json')!=snapshot['controller_state_sha256']):
        raise ValueError('learning controller moved from the frozen monitor checkpoint')
    config=json.loads(Path(plan['config']).read_text());stage=plan['stage']
    if stage not in ('monitor_preflight','monitor_generate') or config['stage']!=stage:
        raise ValueError('undeclared monitor device stage')
    if (config['condition']!='v2-S2' or config['learning_phase']!='pilot'
            or any(config[k]!=snapshot[k] for k in ('arm','run_seed','update'))):
        raise ValueError('monitor runtime identity changed')
    contract=lp['configuration']['training_runtime_contract']
    if any(config.get(k)!=v for k,v in contract.items()):raise ValueError('monitor numerical or sampler contract differs from LP')
    if config['model']!=snapshot['model'] or config['model_binding_sha256']!=snapshot['model_binding_sha256']:
        raise ValueError('monitor runtime checkpoint changed')
    runtime_bindings={b['path']:b['sha256'] for b in config['bindings']}
    if len(runtime_bindings)!=len(config['bindings']):raise ValueError('duplicate monitor runtime binding')
    if any(runtime_bindings.get(p)!=sha for p,sha in {**scientific,**inputs}.items()):
        raise ValueError('monitor runtime omitted frozen bindings')
    if inputs.get(config['snapshot'])!=digest(config['snapshot']) or inputs.get(config['cells_path'])!=digest(config['cells_path']):
        raise ValueError('monitor inputs were not frozen before generation')
    reservation=Path(plan['reservation'])
    expected=root/'monitors'/f"update_{snapshot['update']:05d}"/(stage+'.json')
    if reservation.resolve()!=expected.resolve():raise ValueError('monitor reservation moved')
    record=json.loads(reservation.read_text())
    if (record['execution_sha256']!=snapshot['execution_sha256'] or record['snapshot_sha256']!=plan['snapshot_lock']['sha256']
            or record['stage']!=stage or record['configuration_sha256']!=digest(plan['config'])):
        raise ValueError('monitor differs from its exclusive reservation')
    if stage=='monitor_generate':
        prior=root/'monitors'/f"update_{snapshot['update']:05d}"/'monitor_preflight'
        health=prior/'health/preflight.json';closed=prior/'dispatch/result.json'
        if any(runtime_bindings.get(str(p))!=digest(p) for p in (health,closed)):
            raise ValueError('monitor preflight evidence is unbound')
        check_preflight({'path':str(health),'sha256':digest(health)})
        result=json.loads(closed.read_text())
        if (result.get('status')!='RUNTIME_EXITED_ZERO' or result.get('cleanup_verified') is not True
                or result.get('snapshot_sha256')!=plan['snapshot_lock']['sha256']):
            raise ValueError('same-snapshot non-probe preflight has not passed cleanly')
    lease=json.loads(Path(config['lease_path']).read_text())
    canonical=json.loads((Path(plan['lease_root'])/(lease['id']+'.json')).read_text())
    if (lease!=canonical or lease['phase']!='v2-S2-learning-pilot' or lease['owner']!='e13v2'
            or lease['status']!='ACTIVE' or lease['id']!=config['lease_id'] or lease['host']!=socket.gethostname().split('.')[0]
            or lease['run_key']!=f"{run['arm']}/{run['run_seed']}/{snapshot['update']}/{stage}"):
        raise ValueError('monitor device is not its canonical local learning allocation')
    maximum=plan['maximum_seconds']
    if not 90<maximum<=lease['expires_unix']-lease['started_unix']:raise ValueError('monitor exceeds its lease')
    if record['lease_id']!=lease['id'] or record['maximum_seconds']!=maximum:raise ValueError('monitor resource reservation changed')
    return config,lease,record


def launch_reserved(plan):
    config, lease, reservation = authorize(plan)
    root = Path(plan['dispatch_root']); root.mkdir(parents=True, exist_ok=False)
    result = {'condition': 'v2-S2', 'phase': plan['run']['phase'], 'arm': plan['run']['arm'],
              'run_seed': plan['run']['run_seed'], 'update': config['update'], 'stage': plan['stage'],
              'lease_id': lease['id'], 'automatic_retry': False, 'status': 'INCOMPLETE_INFRA',
              'snapshot_sha256':plan['snapshot_lock']['sha256'], 'model_binding_sha256':config['model_binding_sha256']}
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
            child = subprocess.Popen([config['python'], str(HERE/'monitor_runtime.py'), '--config', plan['config'],
                '--stage', plan['stage']], env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            write_new(root/'process.json', {'pid': child.pid, 'marker': lease['id'],
                'start_ticks': Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19],
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
            result['worker_exit_code'] = child.wait(timeout=remaining)
        if result['worker_exit_code']: raise RuntimeError('monitor runtime exited nonzero; retained snapshot is not retried')
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


def launch(plan):
    # Hold the same fence for the whole stage: training cannot advance while a
    # diagnostic checkpoint is in use, including on exceptional exits.
    _,execution,_=verify_learning(plan['run']);run=plan['run']
    root=Path(execution['configuration']['ledger'])/'pilot'/run['arm']/str(run['run_seed'])
    with (root/'controller.lock').open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return launch_reserved(plan)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    result = launch(json.loads(args.plan.read_text()))
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result['status'] == 'RUNTIME_EXITED_ZERO' else 1)
