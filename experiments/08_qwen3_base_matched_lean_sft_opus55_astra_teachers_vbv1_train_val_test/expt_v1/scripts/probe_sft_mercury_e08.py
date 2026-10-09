#!/usr/bin/env python3
"""Run the admitted disposable Mercury layout probe once, with a lease and bounded cleanup."""
from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

R = Path('/lfs/mercury2/0/brando9/rl4cv_e08_layout')
S = Path('/dfs/scratch0/brando9/rl4cv_e08_layout_10-09-2026')
PY = R / 'venvs/nemo_rl.models.policy.dtensor_policy_worker.DTensorPolicyWorker/bin/python'
CHECKPOINTS = Path('/dev/shm/rl4cv_e08_layout_8339_attempt4/checkpoints')
DEVICES = list(range(8))
TAG = 'e08-mercury-disposable-8339e1ac-9675-4e2c-b609-552c1b436a12-attempt4'
RAY_TMP = f'/tmp/e8m4_{os.getuid()}'
PRIOR_SECONDS = 1189.9956840518862
BUDGET_SECONDS = 610.0043159481138
CLEANUP_RESERVE_SECONDS = 20
MIN_AVAILABLE_BYTES = 20 * 2**30
BOOT = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
HOST = os.uname().nodename
REGISTRY = R / 'pipeline/leases.json'
LOCK = R / 'pipeline/lock'
REPORT = R / 'execution_attempt4.json'
known = {}
report = {'status': 'PRECHECK', 'steps': [], 'devices': DEVICES,
          'prior_probe_seconds': PRIOR_SECONDS, 'budget_seconds': BUDGET_SECONDS,
          'cleanup_reserve_seconds': CLEANUP_RESERVE_SECONDS, 'task_tag': TAG}


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(path):
    with Path(path).open('rb') as stream:
        value = hashlib.sha256()
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            value.update(chunk)
        return value.hexdigest()


def atomic(path, value):
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def save():
    atomic(REPORT, report)


def proc(pid):
    try:
        p = Path(f'/proc/{pid}')
        if p.stat().st_uid != os.getuid():
            return None
        fields = (p / 'stat').read_text().rsplit(')', 1)[1].split()
        return {'pid': int(pid), 'pid_start': fields[19], 'ppid': int(fields[1]),
                'state': fields[0], 'boot_id': BOOT, 'host': HOST}
    except (OSError, ValueError, IndexError):
        return None


def owned():
    current = {}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        ident = proc(p.name)
        if not ident or ident['state'] == 'Z':
            continue
        current[ident['pid']] = ident
        try:
            env = (p / 'environ').read_bytes().split(b'\0')
            tagged = f'E08_TASK_TAG={TAG}'.encode() in env or f'RAY_TMPDIR={RAY_TMP}'.encode() in env
        except OSError:
            tagged = False
        if tagged or known.get(ident['pid'], {}).get('pid_start') == ident['pid_start']:
            known[ident['pid']] = ident
    # Include currently visible descendants even if a child sanitizes its environment.
    changed = True
    while changed:
        changed = False
        for pid, ident in current.items():
            parent = current.get(ident['ppid'])
            parent_owned = parent and known.get(ident['ppid'], {}).get('pid_start') == parent['pid_start']
            if pid not in known and (ident['ppid'] == os.getpid() or parent_owned):
                known[pid] = ident
                changed = True
    return {pid: ident for pid, ident in current.items()
            if known.get(pid, {}).get('pid_start') == ident['pid_start']}


def terminate_owned():
    initial = owned()
    for pid, ident in initial.items():
        if (proc(pid) or {}).get('pid_start') == ident['pid_start']:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    until = time.monotonic() + 3
    while time.monotonic() < until and owned():
        time.sleep(0.1)
    killed = []
    for _ in range(3):
        remaining = owned()
        if not remaining:
            break
        for pid, ident in remaining.items():
            if (proc(pid) or {}).get('pid_start') == ident['pid_start']:
                try:
                    os.kill(pid, signal.SIGKILL)
                    killed.append(pid)
                except ProcessLookupError:
                    pass
        time.sleep(0.3)
    return {'term_identities': list(initial.values()), 'kill_pids': killed,
            'remaining_owned_identities': list(owned().values())}


def query(fields, kind='gpu', timeout=5):
    command = ['nvidia-smi', f'--query-{kind}={fields}', '--format=csv,noheader,nounits']
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'nvidia-smi failed: {result.returncode}: {result.stderr[:500]}')
    return result.stdout


def survey():
    devices = {}
    rows = query('index,uuid,memory.used,memory.free,utilization.gpu,utilization.memory')
    for line in rows.splitlines():
        fields = [x.strip() for x in line.split(',')]
        if len(fields) != 6 or not fields[0].isdigit() or not fields[1].startswith('GPU-'):
            raise RuntimeError(f'malformed device inventory: {line!r}')
        devices[int(fields[0])] = fields
    if not set(DEVICES).issubset(devices):
        raise RuntimeError('requested devices absent from inventory')
    apps = query('gpu_uuid,pid,used_gpu_memory', 'compute-apps')
    by_uuid = {v[1]: k for k, v in devices.items()}
    processes = []
    for line in apps.splitlines():
        fields = [x.strip() for x in line.split(',')]
        if len(fields) != 3 or fields[0] not in by_uuid or not fields[1].isdigit():
            raise RuntimeError(f'malformed process inventory: {line!r}')
        pid = int(fields[1])
        processes.append({'device': by_uuid[fields[0]], 'pid': pid, 'memory_mib': fields[2],
                          'identity_if_same_user': proc(pid)})
    mem = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, rest = line.split(':', 1)
        if key in ('MemAvailable', 'MemTotal', 'Shmem', 'SwapFree'):
            mem[key + '_bytes'] = int(rest.strip().split()[0]) * 1024
    return {'time': time.time(), 'utc': utc(), 'gpus': devices, 'compute_processes': processes,
            'host_memory': mem, 'load': Path('/proc/loadavg').read_text().strip(),
            'cpu_pressure': Path('/proc/pressure/cpu').read_text().strip(),
            'cpu_times': Path('/proc/stat').read_text().splitlines()[0],
            'owned': list(owned().values())}


def load_registry():
    return json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}


def live(lease):
    if lease.get('released'):
        return False
    if lease.get('expires_epoch', float('inf')) < time.time():
        return False
    ident = lease.get('identity')
    if ident and ident.get('host') == HOST and ident.get('boot_id') == BOOT:
        actual = proc(ident['pid'])
        return bool(actual and actual['pid_start'] == ident.get('pid_start'))
    return True


def interrupted(signum, _frame):
    raise InterruptedError(f'received signal {signum}')


def main():
    if HOST.split('.')[0] != 'mercury2':
        raise RuntimeError('this runner is restricted to mercury2')
    R.mkdir(parents=True, exist_ok=True)
    # O_EXCL provides a durable no-restart gate even for simultaneous launch attempts.
    with REPORT.open('x') as stream:
        json.dump(report, stream)
    report.update(identity=proc(os.getpid()), script_sha256=digest(__file__), started_utc=utc())
    save()
    acquired = False
    start = None
    try:
        receipt_path = R / 'environment_receipt.json'
        receipt = json.loads(receipt_path.read_text())
        assert receipt['versions']['torch'] == '2.7.1+cu128'
        assert receipt['versions']['transformers'] == '4.55.4'
        assert receipt['versions']['nemo_rl'] == '0.4.0'
        assert receipt['model_revision'] == '0b0bd3732e2c374d483664439ea334928b65f304'
        assert receipt['cuda_initialized'] is False
        assert receipt['model_files'] and all(v['matches'] for v in receipt['model_files'].values())
        assert receipt['parallelizer_sha256'] == '366965e7d9b6360fdd845b559f8b46ce17845088dbf4e12626c0e23192dd37bd'
        assert digest(R / 'nemo_rl/nemo_rl/models/dtensor/parallelize.py') == receipt['parallelizer_sha256']
        assert PY.is_file() and (R / 'probe_attempt4.yaml').is_file()
        assert not CHECKPOINTS.exists(), 'refusing old disposable checkpoints'
        report['cpu_environment_check'] = {'status': 'PASS', 'receipt': str(receipt_path), 'sha256': digest(receipt_path)}
        report['input_hashes'] = {str(p): digest(p) for p in
            (R / 'probe_attempt4.yaml', R / 'hooks_attempt4/sitecustomize.py', R / 'hooks_attempt4/e08_whole_layer.py', R / 'train6.jsonl', R / 's_v1_val_dummy.jsonl')}
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        with LOCK.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            before = survey()
            report['preallocation_survey'] = before
            leases = load_registry()
            busy = {g for lease in leases.values() if live(lease) for g in lease['gpus']}
            assert not any(p['device'] in DEVICES for p in before['compute_processes']), 'compute process occupies requested device'
            assert not set(DEVICES) & busy, 'requested device has a live lease'
            assert before['host_memory']['MemAvailable_bytes'] >= MIN_AVAILABLE_BYTES
            assert not owned(), 'prior task descendants still running'
            start = time.monotonic()
            deadline = start + BUDGET_SECONDS - CLEANUP_RESERVE_SECONDS
            report.update(started_epoch=time.time(), status='LEASED', deadline_epoch=time.time() + BUDGET_SECONDS)
            lease = {'owner': TAG, 'kind': 'disposable-tp8-cpu-offload-whole-layer-checkpoint',
                     'gpus': DEVICES, 'identity': proc(os.getpid()), 'since': utc(),
                     'expires_epoch': time.time() + BUDGET_SECONDS, 'released': False,
                     'prior_probe_seconds': PRIOR_SECONDS, 'budget_seconds': BUDGET_SECONDS}
            leases[TAG] = lease
            atomic(REGISTRY, leases)
            acquired = True
            report['lease'] = lease
            save()
        CHECKPOINTS.mkdir(parents=True)
        env = dict(os.environ)
        env.update(CUDA_VISIBLE_DEVICES=','.join(map(str, DEVICES)), HF_HUB_OFFLINE='1',
                   HF_HOME=str(S / 'hf_cache'), NEMO_RL_VENV_DIR=str(R / 'venvs'),
                   PYTHONPATH=str(R / 'nemo_rl'), RAY_ADDRESS='local', RAY_TMPDIR=RAY_TMP,
                   E08_TASK_TAG=TAG, E08_MODEL_PATH=str(S / 'model'),
                   E08_CHECKPOINT_DIR=str(CHECKPOINTS), E08_LOG_DIR=str(R / 'logs'),
                   E08_TENSORBOARD_DIR=str(R / 'tb'), E08_RUN_NAME=TAG,
                   E08_TRAIN_JSONL=str(R / 'train6.jsonl'), E08_VAL_JSONL=str(R / 's_v1_val_dummy.jsonl'),
                   OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4')
        env.pop('E08_LAYOUT_PROBE', None)
        env.pop('E08_WHOLE_LAYER_CHECKPOINT', None)
        for target in (2, 3):
            if time.monotonic() >= deadline:
                report['status'] = 'TIMEOUT'
                break
            if target == 3:
                assert (CHECKPOINTS / 'step_2/policy/weights/.metadata').is_file(), 'step-2 weights absent'
                assert (CHECKPOINTS / 'step_2/policy/optimizer/.metadata').is_file(), 'step-2 optimizer absent'
            command = [str(PY), '-u', str(R / 'nemo_rl/examples/run_sft.py'), '--config', str(R / 'probe_attempt4.yaml'), f'sft.max_num_steps={target}']
            if target == 3:
                command.append('checkpointing.enabled=false')
            log_path = R / f'to_step_{target}_attempt4.log'
            segment_start = time.monotonic()
            report.update(status='RUNNING', pending_command=command)
            save()
            with log_path.open('x') as log:
                child = subprocess.Popen(command, cwd=R / 'nemo_rl', env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                ident = proc(child.pid)
                assert ident is not None
                known[child.pid] = ident
                report['driver'] = {'identity': ident, 'target_step': target}
                save()
                next_sample = 0
                while child.poll() is None:
                    if time.monotonic() >= deadline:
                        report['status'] = 'TIMEOUT'
                        break
                    if time.monotonic() >= next_sample:
                        sample = survey()
                        with (R / 'resources_attempt4.jsonl').open('a') as stream:
                            stream.write(json.dumps(sample) + '\n')
                        if sample['host_memory']['MemAvailable_bytes'] < MIN_AVAILABLE_BYTES:
                            report['status'] = 'HOST_MEMORY_GUARD'
                            break
                        ours = set(owned())
                        if any(p['device'] in DEVICES and p['pid'] not in ours for p in sample['compute_processes']):
                            report['status'] = 'FOREIGN_PROCESS_DETECTED'
                            break
                        next_sample = time.monotonic() + 10
                    time.sleep(0.5)
                cleanup = terminate_owned()
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
            row = {'target': target, 'exit': child.returncode, 'seconds': time.monotonic() - segment_start,
                   'log': str(log_path), 'sha256': digest(log_path), 'cleanup': cleanup}
            report['steps'].append(row)
            save()
            if child.returncode != 0 or report['status'] != 'RUNNING' or cleanup['remaining_owned_identities']:
                if report['status'] == 'RUNNING':
                    report['status'] = 'FAILED'
                break
        else:
            report['status'] = 'EXECUTION_COMPLETE_PENDING_ADMISSION'
    except BaseException as exc:
        report.update(status='INTERRUPTED' if isinstance(exc, InterruptedError) else 'FAILED', error=repr(exc))
    finally:
        if acquired:
            report['final_cleanup'] = terminate_owned()
            report['remaining_owned_pids'] = sorted(owned())
            elapsed = time.monotonic() - start
            report.update(elapsed_seconds=elapsed, cumulative_probe_seconds=PRIOR_SECONDS + elapsed,
                          device_seconds=8 * elapsed, finished_utc=utc())
            with LOCK.open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                leases = load_registry()
                leases[TAG].update(released=not bool(report['remaining_owned_pids']), released_at=utc(), elapsed_seconds=elapsed)
                atomic(REGISTRY, leases)
                report['lease_released'] = leases[TAG]['released']
            if report['remaining_owned_pids']:
                report['status'] = 'CLEANUP_INCOMPLETE'
        else:
            report.update(elapsed_seconds=0, cumulative_probe_seconds=PRIOR_SECONDS, lease_released=False, finished_utc=utc())
        save()
    return 0 if report['status'] == 'EXECUTION_COMPLETE_PENDING_ADMISSION' else 3


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    raise SystemExit(main())
