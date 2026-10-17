"""Finish reporting and subsequent gates from retained completed T2 stages without repeating an update."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import time

from technical import ROOT, T2, T3, V3, execute, measure_t2
from cohort import digest
from training_checkpoint import write_new


def finish(device):
    lock = (ROOT / f'gpu_{device}.lock').open('a')
    deadline = time.monotonic() + 10 * 3600
    while True:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                raise TimeoutError('original controller exceeded its technical allocation')
            time.sleep(15)
    # A terminated controller is not sufficient: every expensive stage must have
    # its original successful execution receipt. Never replay a failed stage.
    for stage in ('update', 'export', 'generate_refit', 'probabilities_refit'):
        receipt = json.loads((T2 / stage / 'execution.json').read_text())
        if receipt['exit_code'] != 0:
            raise RuntimeError('original stage did not finish: ' + stage)
    if (T2 / 'result.json').exists():
        result = json.loads((T2 / 'result.json').read_text())
    else:
        result = measure_t2()
    from reporting import publish_t2
    publish_t2()
    if result['status'] != 'PASS': return result
    if not (T3 / 'result.json').exists():
        if (T3 / 'replay').exists():
            raise RuntimeError('an earlier replay needs explicit reconciliation; not repeated')
        uuid, memory = subprocess.check_output(['nvidia-smi', f'--id={device}',
            '--query-gpu=uuid,memory.used', '--format=csv,noheader,nounits'], text=True).strip().split(',')
        if int(memory) > 100: raise RuntimeError('device is no longer idle')
        T3.mkdir(parents=True, exist_ok=True)
        identity = f'e13v3-T3-{os.getpid()}'
        lease = T3 / 'lease.json'
        started = time.time()
        write_new(lease, {'owner': 'e13v3', 'id': identity, 'status': 'ACTIVE', 'index': device,
                         'uuid': uuid.strip(), 'started_unix': started, 'expires_unix': started + 4 * 3600})
        os.environ.update(CUDA_VISIBLE_DEVICES=str(device), CUDA_DEVICE_ORDER='PCI_BUS_ID', E13_EXECUTION_ID=identity)
        try:
            execute('replay', T3 / 'replay', lease, source_update=str(T2 / 'update/output'))
            from technical_measurements import t3
            result = t3(json.loads((T2 / 'update/output/result.json').read_text()),
                        json.loads((T3 / 'replay/output/result.json').read_text()),
                        source_result_sha256=digest(T2 / 'update/output/result.json'))
            result.update(condition='v3-A7', api_spend_usd=0)
            write_new(T3 / 'result.json', result)
            write_new(V3 / 'results/T3_v3.json', result)
        finally:
            write_new(T3 / 'lease_end.json', {'id': identity, 'ended_unix': time.time(),
                'device_hours': (time.time() - started) / 3600,
                'gpu_census': subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                                                       '--format=csv,noheader,nounits'], text=True)})
    else:
        result = json.loads((T3 / 'result.json').read_text())
    fcntl.flock(lock, fcntl.LOCK_UN)
    if result['status'] == 'PASS':
        from evaluation_probe import run
        return run(device)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', type=int, choices=[0, 5, 7], default=0)
    args = parser.parse_args()
    print(json.dumps(finish(args.device), sort_keys=True))
