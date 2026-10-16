"""Run frozen validation generation remotely; return only exact verified raw cells."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from recovery_watch import alive, identity, read, write
from remote_training import ssh, snapshot_wrapper

HERE = Path(__file__).resolve().parent
LOCAL = Path('/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3')
SHARED = Path('/dfs/scratch0/brando9/rl4cv_e08_v3_remote')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def system(label):
    return next(s for s in read(HERE / 'results/ladder_manifest_v3.json')['systems'] if s['label'] == label)


def validate_raw(path, label, ids, prompt_hashes, model_paths=None):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    keys = [(row['task_id'], row['sample_idx']) for row in rows]
    expected = {(task, sample) for task in ids for sample in range(8)}
    assert len(rows) == len(set(keys)) == 1080 and set(keys) == expected, 'Missing, extra or duplicate cells'
    for row in rows:
        assert row['label'] == label + '_g8' and row['backend'] == 'vllm'
        if model_paths is not None:
            assert row['model'] in model_paths and row['revision'] is None, 'Wrong exported model'
        assert row['sampling'] == {'temperature': 0.6, 'top_p': 0.95, 'top_k': 20,
                                   'max_tokens': 12288, 'seed': 91 * 100003 + row['sample_idx'],
                                   'thinking': 'on', 'stop_tokens': ['<|im_end|>']}
        assert 0 <= row['generated_tokens'] <= 12288
        for key, value in prompt_hashes[row['task_id']].items():
            assert row[key] == value, (row['task_id'], key)
    return {'cells': len(rows), 'sha256': digest(path), 'sampling_and_prompts_match': True}


def sync_raw(label):
    ready = read(SHARED / 'sft_v3/remote_generation_ready.json')
    ids_path = Path(ready['repo']) / 'experiments' / HERE.parent.name / 'expt_v1/results/split/vbv1_validation_task_ids.txt'
    if not ids_path.exists():
        raise RuntimeError('Frozen validation IDs unavailable')
    ids = ids_path.read_text().splitlines()
    source = SHARED / 'sft_v3/ladder/validation/raw' / f'gen_{label}_g8.jsonl'
    record = read(SHARED / 'sft_v3' / f'remote_gen_{label}.json')
    checked = validate_raw(source, label, ids, read(SHARED / 'sft_v3/generation_prompt_hashes.json'), [record['model']])
    canonical = LOCAL / 'ladder/validation/raw' / source.name
    canonical.parent.mkdir(parents=True, exist_ok=True)
    if canonical.exists():
        assert digest(canonical) == checked['sha256'], 'A different canonical raw file already exists'
    else:
        temp = canonical.with_name(canonical.name + '.transfer')
        shutil.copy2(source, temp)
        assert digest(temp) == checked['sha256']
        os.replace(temp, canonical)
    checked.update(label=label, host=record['host'], gpus=record['gpus'],
                   tensor_parallel_size=record['tensor_parallel_size'], source=str(source),
                   canonical=str(canonical), export_sha256=record['export_sha256'],
                   identity=record['identity'], test_split_opened=False, copied_unix=time.time())
    write(HERE / 'results' / f'remote_generation_{label}.json', checked)
    return checked


def remote(args):
    root = SHARED / 'sft_v3'
    path = root / f'remote_gen_{args.label}.json'
    record = read(path, {})
    if args.probe:
        record['alive'] = alive(record.get('identity'))
        print(json.dumps(record)); return 0
    with (root / 'remote_admission.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        record = read(path, {})
        if record:
            print(json.dumps(record)); return 0
        ready = read(root / 'remote_generation_ready.json', {})
        host = socket.gethostname().split('.')[0]
        if ready.get('status') != 'PASS' or host not in ready.get('verified_hosts', []):
            print(json.dumps({'status': 'WAITING_PREFLIGHT', 'host': host})); return 0
        spec = system(args.label)
        model = SHARED / 'sft_v3' / Path(spec['hf_path']).relative_to(LOCAL)
        if not (model / 'SHA256SUMS').exists():
            print(json.dumps({'status': 'WAITING_EXPORT', 'host': host})); return 0
        inventory = subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.total,uuid',
                                             '--format=csv,noheader,nounits'], text=True)
        devices = [[x.strip() for x in row.split(',')] for row in inventory.splitlines() if row.strip()]
        busy = set(subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid',
                                           '--format=csv,noheader'], text=True).split())
        assert len(devices) == 8 and all(len(d) == 3 and d[0].isdigit() and d[1].isdigit()
                                       and d[2].startswith('GPU-') for d in devices)
        assert busy.issubset({d[2] for d in devices})
        reserved = set()
        for other in root.glob('remote_*.json'):
            job = read(other, {})
            if job.get('host') == host and alive(job.get('identity')):
                reserved.update(job.get('gpus', '').split(','))
        available = [d[0] for d in devices if d[2] not in busy and d[0] not in reserved and int(d[1]) >= 79000]
        needed = 1 if spec['size'] in ('1.7B', '4B') else 4
        if len(available) < needed:
            print(json.dumps({'status': 'WAITING_DEVICES', 'host': host})); return 0
        gpus = ','.join(available[:needed])
        environment = ready['host_environments'][host]
        env = os.environ.copy()
        env.update(E08_WORK=str(SHARED), E08_REPO=ready['repo'], E08_PACK_ROOT=ready['pack'],
                   E08_VERIBENCH_ROOT=ready['veribench_root'], E08_GEN_PYTHON=environment['python'],
                   E08_CACHE_ROOT=environment['root'] + '/cache',
                   E08_FLASHINFER_WORKSPACE=environment['root'] + '/flashinfer/' + args.label,
                   BATCH='1024', CUDA_VISIBLE_DEVICES=gpus)
        receipt = root / f'remote_gen_{args.label}.exit.json'
        wrapper, wrapper_sha = snapshot_wrapper('run_validation.sh', args.label)
        command = ['/usr/bin/python3', str(HERE / 'job_process.py'), '--receipt', str(receipt), '--',
                   'bash', str(wrapper), 'validation', args.label, str(model), 'local', gpus,
                   str(needed), 'generation']
        with (root / f'remote_gen_{args.label}.log').open('a') as log:
            child = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
        record = {'status': 'RUNNING', 'host': host, 'identity': identity(child.pid), 'gpus': gpus,
                  'tensor_parallel_size': needed, 'started_unix': time.time(), 'receipt': str(receipt),
                  'export_sha256': digest(model / 'SHA256SUMS'), 'model': str(model),
                  'wrapper_snapshot': str(wrapper), 'wrapper_sha256': wrapper_sha}
        write(path, record); print(json.dumps(record)); return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label')
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--probe', action='store_true')
    args = parser.parse_args()
    if args.remote:
        return remote(args)
    spec = system(args.label)
    source = Path(spec['hf_path'])
    dest = SHARED / 'sft_v3' / source.relative_to(LOCAL)
    # Whole verified exports only. A half-copied directory never serves a model.
    with (SHARED / 'sft_v3' / f'export_transfer_{args.label}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not (dest / 'SHA256SUMS').exists():
            temp = dest.with_name('.generation_transfer_' + dest.name)
            temp.mkdir(parents=True, exist_ok=True)
            subprocess.run(['rsync', '-a', str(source) + '/', str(temp) + '/'], check=True)
            subprocess.run(['sha256sum', '--check', '--quiet', 'SHA256SUMS'], cwd=temp, check=True)
            os.replace(temp, dest)
        assert digest(source / 'SHA256SUMS') == digest(dest / 'SHA256SUMS')
    deadline = read(LOCAL / 'recovery_config.json')['recovery_deadline_unix']
    path = SHARED / 'sft_v3' / f'remote_gen_{args.label}.json'
    remote_script = SHARED / 'code/expt_v3/remote_generation.py'
    while time.time() < deadline:
        record = read(path, {})
        if record:
            observed = ssh(record['host'], ['/usr/bin/python3', str(remote_script), args.label, '--remote', '--probe'])
            if not observed['alive']:
                receipt = read(Path(record['receipt']), {})
                if receipt.get('identity') != record['identity'] or 'exit_code' not in receipt:
                    raise RuntimeError('Remote generator disappeared without an exact exit receipt; reconcile before restart')
                if receipt['exit_code']:
                    return receipt['exit_code']
                checked = sync_raw(args.label)
                record.update(status='DONE', ended_unix=time.time(), raw_receipt=checked)
                write(path, record); return 0
        elif read(SHARED / 'sft_v3/remote_generation_ready.json', {}).get('status') == 'PASS':
            foreign = Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/leases')
            for host in ('skampere3', 'skampere2'):
                with (foreign / 'registry.lock').open('a') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    leases = read(foreign / 'registry.json', {'leases': []})['leases']
                    if any(r['status'] != 'RELEASED' and r['host'].split('.')[0] == host for r in leases):
                        continue
                    observed = ssh(host, ['/usr/bin/python3', str(remote_script), args.label, '--remote'])
                print(json.dumps(observed), flush=True)
                if observed.get('identity'):
                    break
        time.sleep(60)
    raise RuntimeError('Original recovery deadline reached; no additional generation admission')


if __name__ == '__main__':
    raise SystemExit(main())
