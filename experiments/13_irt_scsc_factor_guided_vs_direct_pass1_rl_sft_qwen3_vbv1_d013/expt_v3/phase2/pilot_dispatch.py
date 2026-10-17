"""Watch technical completion and execute every admitted paired trajectory with retained failure receipts."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from technical import ROOT, V3
from training_checkpoint import write_new


def alive(pid, start_ticks):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return fields[0] != 'Z' and fields[19] == start_ticks
    except FileNotFoundError:
        return False


def trajectory(arm, seed, horizon):
    root = ROOT / 'phase2/pilot_dispatch'
    key = f'{arm}_{seed}_{horizon}'
    attempt = root / key
    attempt.mkdir(parents=True, exist_ok=False)
    admission = ROOT / 'phase2/pilot_admission.json'
    try:
        commands = [
            [sys.executable, str(V3 / 'phase2/pilot_run.py'), '--arm', arm, '--seed', str(seed),
             '--horizon', str(horizon), '--admission', str(admission)],
            [sys.executable, str(V3 / 'phase2/pilot_evaluation.py'), '--arm', arm, '--seed', str(seed),
             '--boundary', str(horizon), '--admission', str(admission)],
        ]
        for stage, command in zip(('train', 'validation'), commands):
            with (attempt / f'{stage}.log').open('x') as log:
                child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                         env={**os.environ, 'CUDA_VISIBLE_DEVICES': ''})
                write_new(attempt / f'{stage}_launch.json', {'pid': child.pid, 'started_unix': time.time(), 'command': command})
                code = child.wait()
                write_new(attempt / f'{stage}_exit.json', {'exit_code': code, 'finished_unix': time.time()})
                if code: raise RuntimeError(f'{key} {stage} exited {code}; see retained log')
        validation = json.loads((ROOT / 'phase2/validation' / key / 'result.json').read_text())
        result = {'arm': arm, 'seed': seed, 'horizon': horizon, 'status': 'LOCAL_TRAJECTORY_COMPLETE',
                  'official_SCSC': validation['official_SCSC_status']}
    except Exception as exc:
        result = {'arm': arm, 'seed': seed, 'horizon': horizon, 'status': 'INCOMPLETE',
                  'error_type': type(exc).__name__, 'error': str(exc)}
    write_new(attempt / 'result.json', result)
    return result


def dispatch(pid, start_ticks):
    root = ROOT / 'phase2/pilot_dispatch'
    root.mkdir(parents=True, exist_ok=False)
    write_new(root / 'watch.json', {'watched_pid': pid, 'start_ticks': start_ticks,
              'started_unix': time.time(), 'api_spend_usd': 0, 'mode': 'watch death and gate receipts'})
    deadline = time.monotonic() + 12 * 3600
    while alive(pid, start_ticks):
        if time.monotonic() >= deadline: raise TimeoutError('technical follow-through exceeded twelve-hour watch')
        time.sleep(30)
    # Completion of a process is never interpreted as successful measurement.
    from resource_plan import prepare
    gate = prepare()
    if gate['status'] != 'PASS':
        write_new(root / 'result.json', {'condition': 'v3-A7', 'status': 'STOPPED_AT_LOCAL_COST_GATE', 'gate': gate})
        return
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(lambda x: trajectory(*x),
                    [(arm, seed, 30) for seed in (1301, 1302) for arm in ('B', 'A', 'P')]))
    if all(r['status'] == 'LOCAL_TRAJECTORY_COMPLETE' for r in rows):
        t5 = json.loads((ROOT / 'phase2/pilot/B_1301/T5_30.json').read_text())
        if t5['status'] == 'EXTEND_TO_60':
            with ThreadPoolExecutor(max_workers=2) as pool:
                rows += list(pool.map(lambda seed: trajectory('B', seed, 60), (1301, 1302)))
    complete = all(r['status'] == 'LOCAL_TRAJECTORY_COMPLETE' for r in rows)
    status = 'COMPLETE' if complete and all(r['official_SCSC'] == 'DETERMINED_FROM_LOCAL_FACTORS' for r in rows) else 'LOCAL_RUNS_COMPLETE_OFFICIAL_SCSC_PENDING' if complete else 'INCOMPLETE'
    result = {'condition': 'v3-A7', 'status': status,
              'runs': rows, 'api_spend_usd': 0, 'finished_unix': time.time()}
    write_new(root / 'result.json', result)
    write_new(V3 / 'results/pilot_dispatch.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--technical-pid', type=int, required=True)
    parser.add_argument('--start-ticks', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(dispatch(args.technical_pid, args.start_ticks), sort_keys=True))
    except Exception as exc:
        write_new(ROOT / 'phase2/pilot_dispatch/error.json', {'condition': 'v3-A7', 'status': 'INCOMPLETE',
                  'error_type': type(exc).__name__, 'error': str(exc), 'finished_unix': time.time(), 'api_spend_usd': 0})
        raise
