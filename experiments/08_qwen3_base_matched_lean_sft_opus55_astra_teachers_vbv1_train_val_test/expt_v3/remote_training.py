"""Admit a frozen training layout remotely and verify its exports copied home."""
from __future__ import annotations
import argparse
import fcntl
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import time
from recovery_watch import alive, identity, read, write

HERE = Path(__file__).resolve().parent
LOCAL = Path('/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3')
SHARED = Path('/dfs/scratch0/brando9/rl4cv_e08_v3_remote')
LAYOUTS = {'1p7b': 1, '4b': 2, '8b': 4, '14b': 8}


def ssh(host, command):
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host,
                             shlex.join(command)], capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise RuntimeError(f'{host}: remote exit {result.returncode}: {result.stderr[-1000:]}')
    return json.loads(result.stdout)


def sync_exports(condition, short='14b'):
    label = f'v3_{condition}_{short}'
    source = SHARED / 'sft_v3/ckpt' / label
    target = LOCAL / 'ckpt' / label
    target.mkdir(parents=True, exist_ok=True)
    for name in ('logs', 'driver_logs'):
        if (source / name).exists():
            subprocess.run(['rsync', '-a', str(source / name), str(target) + '/'], check=True)
    steps = (335, 667) if condition == 'E' else (334, 658)
    for step in steps:
        export = source / f'hf/step_{step}'
        dest = target / f'hf/step_{step}'
        if not (export / 'SHA256SUMS').exists() or (dest / 'SHA256SUMS').exists():
            continue
        temporary = target / f'hf/.transfer_step_{step}'
        temporary.mkdir(parents=True, exist_ok=True)
        subprocess.run(['rsync', '-a', str(export) + '/', str(temporary) + '/'], check=True)
        subprocess.run(['sha256sum', '--check', '--quiet', 'SHA256SUMS'], cwd=temporary, check=True)
        temporary.rename(dest)
        print(f'verified and installed {label} step {step}', flush=True)


def remote(args):
    root = SHARED / 'sft_v3'
    short = getattr(args, 'size', '14b')
    needed = LAYOUTS[short]
    path = root / f'remote_{args.condition}_{short}.json'
    record = read(path, {})
    if args.probe:
        record['alive'] = alive(record.get('identity'))
        print(json.dumps(record)); return 0
    with (root / 'remote_admission.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        record = read(path, {})
        if record:
            print(json.dumps(record)); return 0
        ready = read(root / 'remote_ready.json', {})
        host = socket.gethostname().split('.')[0]
        if (ready.get('status') != 'PASS' or host not in ready.get('verified_hosts', [])
                or short not in ready.get('verified_sizes', ['14b'])):
            print(json.dumps({'status': 'WAITING_PREFLIGHT', 'host': host})); return 0
        result = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid', '--format=csv,noheader'],
                                capture_output=True, text=True, check=True)
        inventory = subprocess.run(['nvidia-smi', '--query-gpu=index,memory.total,uuid', '--format=csv,noheader,nounits'],
                                   capture_output=True, text=True, check=True)
        devices = [line.split(',') for line in inventory.stdout.splitlines() if line.strip()]
        busy = set(result.stdout.split())
        if (any(len(d) != 3 or not d[0].strip().isdigit() or not d[1].strip().isdigit()
                or not d[2].strip().startswith('GPU-') for d in devices)
                or not busy.issubset({d[2].strip() for d in devices})):
            raise RuntimeError('Unresolved remote GPU inventory; admission refused')
        reserved = set()
        for other in root.glob('remote_*.json'):
            record_other = read(other, {})
            if record_other.get('host') == host and alive(record_other.get('identity')):
                reserved.update(record_other.get('gpus', '').split(','))
        available = [d for d in devices if len(d) == 3 and d[2].strip() not in busy and d[0].strip() not in reserved]
        if len(devices) != 8 or len(available) < needed or any(int(d[1]) < 79000 for d in available):
            print(json.dumps({'status': 'WAITING_DEVICES', 'host': host})); return 0
        if os.statvfs(SHARED).f_bavail * os.statvfs(SHARED).f_frsize < 1100 * 1024**3:
            raise RuntimeError('Shared storage has less than the reserved 1100 GiB working headroom')
        # Admit only after the local owner holds the shared E13 registry lock.
        gpus = ','.join(d[0].strip() for d in available[:needed])
        env = os.environ.copy(); env.update(E08_WORK=str(SHARED), CUDA_VISIBLE_DEVICES=gpus,
                                           E08_NEMO_ROOT=ready.get('host_environments', {}).get(host, str(SHARED / 'nemo_rl')))
        receipt = root / f'remote_{args.condition}_{short}.exit.json'
        command = ['/usr/bin/python3', str(HERE / 'job_process.py'), '--receipt', str(receipt), '--',
                   'bash', str(HERE / 'train_continuation.sh'), args.condition, short, gpus]
        with (root / f'remote_{args.condition}_{short}.log').open('a') as log:
            child = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
        record = {'status': 'RUNNING', 'host': host, 'identity': identity(child.pid),
                  'gpus': gpus, 'tensor_parallel_size': needed, 'started_unix': time.time(), 'receipt': str(receipt)}
        write(path, record); print(json.dumps(record)); return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('condition', choices=['E', 'R'])
    parser.add_argument('--size', choices=LAYOUTS, default='14b')
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--probe', action='store_true')
    args = parser.parse_args()
    if args.remote:
        return remote(args)
    root = SHARED / 'sft_v3'; root.mkdir(exist_ok=True)
    path = root / f'remote_{args.condition}_{args.size}.json'
    deadline = read(LOCAL / 'recovery_config.json')['recovery_deadline_unix']
    remote_script = SHARED / 'code/expt_v3/remote_training.py'
    while time.time() < deadline:
        record = read(path, {})
        if record:
            observed = ssh(record['host'], ['/usr/bin/python3', str(remote_script), args.condition, '--size', args.size, '--remote', '--probe'])
            sync_exports(args.condition, args.size)
            if not observed['alive']:
                receipt = read(Path(record['receipt']), {})
                if receipt.get('identity') != record['identity'] or 'exit_code' not in receipt:
                    raise RuntimeError('Remote child disappeared without an exact exit receipt; reconcile before restart')
                if receipt['exit_code']:
                    return receipt['exit_code']
                record.update(status='DONE', ended_unix=time.time()); write(path, record)
                return 0
        elif read(root / 'remote_ready.json', {}).get('status') == 'PASS':
            foreign = Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/leases')
            for host in ('skampere2', 'skampere3'):
                with (foreign / 'registry.lock').open('a') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    leases = read(foreign / 'registry.json', {'leases': []})['leases']
                    if any(r['status'] != 'RELEASED' and r['host'].split('.')[0] == host for r in leases):
                        continue
                    observed = ssh(host, ['/usr/bin/python3', str(remote_script), args.condition, '--size', args.size, '--remote'])
                print(json.dumps(observed), flush=True)
                if observed.get('identity'):
                    break
        else:
            print('WAITING_PREFLIGHT: copied environment and baseline must be verified', flush=True)
        time.sleep(300)
    raise RuntimeError('Original recovery deadline reached; no additional remote admission')


if __name__ == '__main__':
    raise SystemExit(main())
