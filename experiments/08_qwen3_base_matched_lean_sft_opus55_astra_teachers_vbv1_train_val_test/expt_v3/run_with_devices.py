"""Run a bounded command under shared device locks, preserving an idle skampere1 GPU."""
from __future__ import annotations
import argparse
from datetime import timedelta
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'expt_v1/scripts'))
import gpu_lease_e08 as leases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n', type=int, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    assert args.n > 0 and args.command
    foreign = Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/leases')
    lease_id = 'e08-v3-' + uuid.uuid4().hex
    with (foreign / 'registry.lock').open('a') as f, leases.LOCK.open('a') as g:
        fcntl.flock(f, fcntl.LOCK_EX)
        fcntl.flock(g, fcntl.LOCK_EX)
        registry = leases.load()
        e13 = json.loads((foreign / 'registry.json').read_text())
        reserved = {r['index'] for r in e13['leases'] if r['status'] != 'RELEASED' and r['host'].split('.')[0] == 'skampere1'}
        reserved |= {gpu for r in leases.live_leases(registry).values() for gpu in r['gpus']}
        table = leases.gpu_table()
        available = [i for i, owners in table.items() if not owners and i not in reserved]
        # Device 0 remains available for the experiment-13 owner even between its leases.
        candidates = [i for i in available if i != 0]
        if len(available) < args.n + 1 or len(candidates) < args.n:
            print(json.dumps({'status': 'WAITING_DEVICES', 'available': available, 'requested': args.n}))
            return 3
        chosen = candidates[:args.n]
        record = {'owner': 'e08-v3', 'stage': args.name, 'gpus': chosen,
                  'identity': leases.identity(os.getpid()), 'since': leases.ts(),
                  'expires_utc': leases.ts(leases.now_utc() + timedelta(hours=6)),
                  'boundary': 'one training continuation or validation rung', 'released': False}
        registry[lease_id] = record
        leases.save(registry)
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = ','.join(map(str, chosen))
    command = [arg.replace('{gpus}', env['CUDA_VISIBLE_DEVICES']) for arg in args.command]
    if command[0] == '--':
        command = command[1:]
    print(json.dumps({'lease_id': lease_id, 'gpus': chosen, 'command': command}), flush=True)
    try:
        return subprocess.run(command, env=env).returncode
    finally:
        with leases.LOCK.open('a') as g:
            fcntl.flock(g, fcntl.LOCK_EX)
            registry = leases.load()
            registry[lease_id].update(released=True, released_at=leases.ts())
            leases.save(registry)


if __name__ == '__main__':
    raise SystemExit(main())
