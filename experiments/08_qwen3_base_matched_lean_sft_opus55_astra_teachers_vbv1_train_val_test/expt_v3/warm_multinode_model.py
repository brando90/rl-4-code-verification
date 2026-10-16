"""Checksum the unchanged baseline into each host's cache before GPU admission."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import time
from recovery_watch import ROOT, identity, read, write

HERE = Path(__file__).resolve().parent
SHARED = Path('/dfs/scratch0/brando9/rl4cv_e08_v3_remote')
MODEL = SHARED / 'ckpt/14B/hf/step_658/pytorch_model.bin'
EXPECTED = '140d9e8d22c741587ddb40c9ffa6140850879a45263a8a6bbd0fcfafbbdb48c3'
HOSTS = ('skampere1', 'skampere2', 'skampere3')


def checked_read(path, expected, deadline):
    before = path.stat(); total = 0; digest = hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            assert time.time() < deadline, 'Original or finite cache-read deadline reached'
            block = stream.read(16 * 1024**2)
            if not block:
                break
            digest.update(block); total += len(block)
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
    assert total == before.st_size and digest.hexdigest() == expected, 'Frozen model checksum mismatch'
    return {'bytes': total, 'sha256': digest.hexdigest(), 'mtime_ns': after.st_mtime_ns}


def worker(root):
    plan = read(root / 'plan.json'); host = socket.gethostname().split('.')[0]
    assert host in HOSTS and plan['expected_sha256'] == EXPECTED
    record = {'status': 'READING', 'host': host, 'identity': identity(os.getpid()),
              'started_unix': time.time(), 'deadline_unix': plan['deadline_unix'], 'gpu_allocations': 0}
    write(root / f'{host}.json', record)
    try:
        record.update(checked_read(MODEL, EXPECTED, plan['deadline_unix']), status='PASS')
    except BaseException as error:
        record.update(status='FAIL', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        record['ended_unix'] = time.time(); write(root / f'{host}.json', record)
    return record


def warm(deadline):
    assert time.time() < deadline
    root = SHARED / 'sft_v3' / f'model_warm_14b_{time.time_ns()}'; root.mkdir()
    source = HERE / 'warm_multinode_model.py'
    (root / source.name).write_bytes(source.read_bytes())
    (root / 'recovery_watch.py').write_bytes((HERE / 'recovery_watch.py').read_bytes())
    plan = {'deadline_unix': min(deadline, time.time() + 1800), 'original_deadline_unix': deadline,
            'expected_sha256': EXPECTED, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'identity': identity(os.getpid()), 'model': str(MODEL), 'gpu_allocations': 0}
    write(root / 'plan.json', plan)
    print(json.dumps({'status': 'MODEL_CACHE_READ_STARTED', 'root': str(root)}), flush=True)
    def launch(host):
        seconds = max(1, int(plan['deadline_unix'] - time.time()))
        command = ['setsid', '--wait', '/usr/bin/python3', str(HERE / 'job_process.py'),
                   '--receipt', str(root / f'{host}.exit.json'), '--',
                   '/usr/bin/timeout', '--kill-after=15s', str(seconds), '/usr/bin/python3',
                   str(root / source.name), '--worker', str(root)]
        # job_process.py is available at the same shared path on all hosts.
        command[3] = str(SHARED / 'code/expt_v3/job_process.py')
        with (root / f'{host}.log').open('w') as log:
            completed = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host,
                                        shlex.join(command)], stdout=log, stderr=subprocess.STDOUT,
                                       timeout=seconds + 45)
        receipt = read(root / f'{host}.exit.json', {})
        assert completed.returncode == receipt.get('exit_code') == 0, f'{host}: cache read failed'
        result = read(root / f'{host}.json')
        assert result['status'] == 'PASS' and result['sha256'] == EXPECTED
        return host, {'read': result, 'exit_receipt': receipt}
    result = {'status': 'STARTING', 'root': str(root), 'plan': plan}
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            result.update(hosts=dict(pool.map(launch, HOSTS)), status='PASS')
    except BaseException as error:
        result.update(status='FAIL', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        result['ended_unix'] = time.time(); write(root / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    args = parser.parse_args()
    print(json.dumps(worker(args.worker) if args.worker else warm(read(ROOT / 'recovery_config.json')['recovery_deadline_unix'])))
