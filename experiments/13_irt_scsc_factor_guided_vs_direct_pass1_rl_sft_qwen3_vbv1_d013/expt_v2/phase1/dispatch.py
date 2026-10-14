"""Dispatch the single published LP-1 attempt on an idle, unreserved leased device."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys

from device_watch import observe
from lease import claim, release
from panel import digest, write_new


def published(plan):
    lock_path = Path(plan['lock'])
    lock = json.loads(lock_path.read_text())
    if lock.get('gate') != 'LP1' or lock.get('status') != 'FROZEN':
        raise RuntimeError('LP-1 lock is not final')
    repository = Path(plan['repository'])
    revision = plan['published_revision']
    subprocess.run(['git', 'merge-base', '--is-ancestor', revision, 'origin/main'], cwd=repository, check=True)
    blob = subprocess.run(['git', 'show', revision+':'+str(lock_path.relative_to(repository))],
                          cwd=repository, capture_output=True, check=True).stdout
    if hashlib.sha256(blob).hexdigest() != digest(lock_path):
        raise RuntimeError('LP-1 lock differs from the published revision')
    for binding in lock['bindings']:
        if digest(binding['path']) != binding['sha256']:
            raise RuntimeError('LP-1 input changed: '+binding['path'])
    if lock['G0_result'] not in {b['path'] for b in lock['bindings']}:
        raise RuntimeError('G0 prerequisite is not bound')
    if json.loads(Path(lock['G0_result']).read_text())['status'] != 'PASS':
        raise RuntimeError('LP-1 requires published G0 PASS')
    if digest(plan['configuration']) != lock['configuration_sha256']:
        raise RuntimeError('dispatch configuration differs from frozen lock')
    return json.loads(Path(plan['configuration']).read_text())


def command(host, argv, **kwargs):
    local = socket.gethostname().split('.')[0] == host
    args = argv if local else ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', host, shlex.join(argv)]
    return subprocess.run(args, **kwargs)


def retire_remote_lease(host, path, lease_id):
    script = ('import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); d=json.loads(p.read_text()); '
              'assert d["id"]==sys.argv[2]; d["status"]="RELEASED"; '
              't=p.with_suffix(".retired.tmp"); t.write_text(json.dumps(d)); t.replace(p)')
    command(host, ['python3', '-c', script, path, lease_id],
            capture_output=True, text=True, check=True, timeout=30)


def dispatch(plan_path):
    plan = json.loads(Path(plan_path).read_text())
    root = Path(plan['state_root']); root.mkdir(parents=True, exist_ok=True)
    with (root/'dispatch.lock').open('a') as stream:
        try: fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return {'status': 'ALREADY_SUPERVISED'}
        if (root/'attempt.json').exists(): return {'status': 'ATTEMPT_ALREADY_RECORDED_NO_RETRY'}
        config = published(plan)
        subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1]/'watchdog_e13v2.py'),
                        '--root', plan['watchdog_root'], '--run', plan['watchdog_run'],
                        'register', '--role', 'lp1-dispatch', '--pid', str(os.getpid())], check=True)
        reasons = []
        for route in config['routes']:
            inventory = observe(route['host'])
            if not inventory['inventory_complete']: continue
            for index in inventory['idle_device_indices']:
                try:
                    lease = claim(plan['lease_root'], inventory, index,
                        sources=config['foreign_registries'], reservation_bindings=config['reservation_bindings'],
                        seconds=config['maximum_seconds'], cumulative_limit_hours=config['cumulative_limit_hours'],
                        storage_required_bytes=route['storage_required_bytes'], minimum_memory_mib=route['minimum_memory_mib'],
                        minimum_host_available_bytes=route.get('minimum_host_available_bytes',0))
                except RuntimeError as exc:
                    reasons.append({'host': route['host'], 'index': index, 'reason': str(exc)})
                    continue
                # A second current process census closes the preparation/claim gap.
                fresh = observe(route['host'])
                if (not fresh['inventory_complete'] or index not in fresh['idle_device_indices']
                        or not any(d['index'] == index and d['uuid'] == lease['uuid'] for d in fresh['devices'])):
                    release(plan['lease_root'], lease['id'], cleanup_verified=True)
                    continue
                host = route['host']; runtime = dict(route['runtime'])
                runtime.update(lease_path=route['lease_path'], maximum_seconds=config['maximum_seconds'])
                payload = json.dumps({'lease': lease, 'config': runtime})
                installer = ('import json,pathlib,sys; d=json.load(sys.stdin); '
                    'p=pathlib.Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True); '
                    'p.write_text(json.dumps(d["lease"])); '
                    'pathlib.Path(sys.argv[2]).write_text(json.dumps(d["config"]))')
                try:
                    command(host, ['python3', '-c', installer, route['lease_path'], route['config_path']],
                            input=payload, text=True, capture_output=True, check=True, timeout=30)
                    write_new(root/'attempt.json', {'lease_id': lease['id'], 'host': host, 'uuid': lease['uuid'],
                                                  'published_revision': plan['published_revision'], 'retries': 0})
                    argv = ['env', 'CUDA_VISIBLE_DEVICES='+lease['uuid'], 'E13_EXECUTION_ID='+lease['id'],
                            *[k+'='+v for k,v in route['environment'].items()],
                            runtime['python'], route['lp1_script'], '--config', route['config_path']]
                    with (root/'execution.log').open('x') as log:
                        result = command(host, argv, stdout=log, stderr=subprocess.STDOUT,
                                         timeout=config['maximum_seconds']+180, check=False)
                    receipt_command = ['python3', '-c', 'import pathlib,sys;print(pathlib.Path(sys.argv[1]).read_text())',
                                       str(Path(runtime['attempt_root'])/'result.json')]
                    retrieved = command(host, receipt_command, capture_output=True, text=True, check=True, timeout=30)
                    receipt = json.loads(retrieved.stdout)
                    receipt['supervisor_exit_code'] = result.returncode
                    if result.returncode != 0 and receipt['status'] == 'PASS':
                        receipt.update(status='INCOMPLETE', probability_status='PASS')
                    write_new(root/'result.json', receipt)
                    clean = bool(receipt.get('cleanup_verified'))
                    if clean:
                        retire_remote_lease(host, route['lease_path'], lease['id'])
                    release(plan['lease_root'], lease['id'], cleanup_verified=clean)
                    return receipt
                except BaseException:
                    # Never silently clear a lease after an unknown remote exit.
                    release(plan['lease_root'], lease['id'], cleanup_verified=False)
                    raise
        return {'status': 'WAIT_FOR_IDLE_UNRESERVED_DEVICE', 'candidate_rejections': reasons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    print(json.dumps(dispatch(parser.parse_args().plan), sort_keys=True))


if __name__ == '__main__':
    main()
