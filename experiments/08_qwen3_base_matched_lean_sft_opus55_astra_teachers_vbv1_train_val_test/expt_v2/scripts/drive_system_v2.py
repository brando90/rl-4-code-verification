#!/usr/bin/env python3
"""Lease idle devices, run the unchanged scientific driver, and release devices when generation merges."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import timedelta

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e08')
RUNTIME = WORK / 'v2'
sys.path.insert(0, str(HERE.parents[1] / 'expt_v1/scripts'))
import gpu_lease_e08 as lease
import test_admission_e08v2 as admission


def main():
    label, model, gpu_csv = sys.argv[1:]
    admission.check(label, model, 'local')
    gpus = [int(g) for g in gpu_csv.split(',')]
    merged = RUNTIME / f'ladder/test/raw/gen_{label}_g8.jsonl'
    state = RUNTIME / 'drivers'
    state.mkdir(exist_ok=True)
    with (state / f'{label}.lock').open('w') as own_lock:
        fcntl.flock(own_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lease_id = None
        if not merged.exists():
            with lease.LOCK.open('a') as shared:
                fcntl.flock(shared, fcntl.LOCK_EX)
                table, registry = lease.gpu_table(), lease.load()
                occupied = {g for v in lease.live_leases(registry).values() for g in v['gpus']}
                if any(g not in table or table[g] or g in occupied for g in gpus):
                    raise RuntimeError(f'Devices {gpus} no longer idle/unleased; no launch')
                now = lease.now_utc()
                lease_id = f'e08v2-{label}-{os.getpid()}'
                registry[lease_id] = dict(owner='e08v2', stage=label, kind='test-generation', gpus=gpus,
                    identity=lease.identity(os.getpid()), since=lease.ts(now), expires_utc=lease.ts(now + timedelta(hours=16)),
                    boundary='release immediately when exact merged generation exists', released=False)
                lease.save(registry)
        env = os.environ.copy()
        env.update(E08_WORK=str(RUNTIME), SCORE_PAR='4', CUDA_VISIBLE_DEVICES=gpu_csv,
                   ELAN_HOME=str(Path.home() / '.elan'))
        cmd = ['bash', str(HERE / 'run_test_e08v2.sh'), 'test', label, model, 'local', gpu_csv, '1']
        log = RUNTIME / f'logs/driver_{label}.log'
        with log.open('a') as out:
            child = subprocess.Popen(cmd, env=env, stdout=out, stderr=subprocess.STDOUT)
            receipt = dict(identity=lease.identity(os.getpid()), child=lease.identity(child.pid), lease_id=lease_id, command=cmd, started=lease.ts())
            (state / f'{label}.json').write_text(json.dumps(receipt, indent=2)+'\n')
            while True:
                code = child.poll()
                if lease_id and (merged.exists() or code is not None):
                    with lease.LOCK.open('a') as shared:
                        fcntl.flock(shared, fcntl.LOCK_EX)
                        lease.release(lease_id)
                    lease_id = None
                if code is not None:
                    receipt.update(exit_code=code, ended=lease.ts())
                    (state / f'{label}.json').write_text(json.dumps(receipt, indent=2)+'\n')
                    return code
                time.sleep(10)


if __name__ == '__main__':
    raise SystemExit(main())
