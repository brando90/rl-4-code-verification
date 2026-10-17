"""Prepare and execute the v3 factored-reward update, refit and deterministic replay without altering v2."""
from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from cohort import SOURCE, digest, retained

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
V2 = V3.parent / 'expt_v2'
ROOT = Path('/lfs/skampere1/0/brando9/rl4cv_e13v3')
T2 = ROOT / 'phase2/technical/T2/attempt_1'
T3 = ROOT / 'phase2/technical/T3/attempt_1'
sys.path.extend([str(V2 / 'phase2'), str(V2 / 'phase1')])
from training_checkpoint import write_new


def prepare():
    groups, receipt = retained()
    target = T2 / 'score'
    target.mkdir(parents=True, exist_ok=False)
    write_new(target / 'groups.json', groups)
    receipt['groups_sha256'] = digest(target / 'groups.json')
    write_new(target / 'cohort.json', receipt)
    public = V3 / 'results'
    public.mkdir(exist_ok=True)
    write_new(public / 'retained_cohort.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('groups', 'generation_bindings')}))


def configuration(stage, root, lease, **overrides):
    original = json.loads((SOURCE / 'update/runtime.json').read_text())
    cfg = {k: v for k, v in original.items() if k not in ('bindings', 'groups_path')}
    cfg.update(stage=stage, stage_root=str(root / 'output'), ray_temp=str(root / 'ray'),
               attempt_root=str(root / 'health'), lease_path=str(lease),
               lease_id=json.loads(lease.read_text())['id'],
               provenance={'condition': 'v3-A7', 'run_seed': original['run_seed'],
                           'stage': stage, 'reward': 'factored_reward',
                           'source_score_sha256': digest(SOURCE / 'score/cells/result.json')})
    cfg.update(overrides)
    paths = list((V2 / 'phase1').glob('*.py')) + list((V2 / 'phase2').glob('*.py')) + list(HERE.glob('*.py'))
    paths.extend([Path(cfg['policy_config']), Path(cfg['train_ids']), Path(cfg['cells_path'])])
    for key in ('groups_path', 'manifest'):
        if cfg.get(key): paths.append(Path(cfg[key]))
    for key in ('initial_model', 'tokenizer', 'model'):
        paths.extend(p for p in Path(cfg[key]).iterdir() if p.is_file())
    if cfg.get('checkpoint'): paths.append(Path(cfg['checkpoint']) / 'receipt.json')
    if cfg.get('source_update'): paths.append(Path(cfg['source_update']) / 'result.json')
    if cfg.get('generation_root'): paths.extend(Path(cfg['generation_root']).glob('*.json'))
    cfg['bindings'] = [{'path': str(p), 'sha256': digest(p)} for p in sorted(set(paths))]
    root.mkdir(parents=True, exist_ok=False)
    write_new(root / 'runtime.json', cfg)
    return cfg


def execute(stage, root, lease, **overrides):
    cfg = configuration(stage, root, lease, **overrides)
    started = time.time()
    command = [cfg['python'], str(HERE / 'backend.py'), '--config', str(root / 'runtime.json')]
    with (root / 'run.log').open('x') as stream:
        child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        write_new(root / 'launch.json', {'pid': child.pid, 'started_unix': started,
                  'stage': stage, 'config_sha256': digest(root / 'runtime.json'),
                  'device': os.environ['CUDA_VISIBLE_DEVICES'], 'api_spend_usd': 0})
        try:
            code = child.wait(timeout=4 * 3600)
        except subprocess.TimeoutExpired:
            # This process group belongs exclusively to this stage.
            import signal
            os.killpg(child.pid, signal.SIGTERM)
            child.wait(timeout=60)
            code = 124
    write_new(root / 'execution.json', {'exit_code': code, 'wall_seconds': time.time() - started,
              'device_hours': (time.time() - started) / 3600, 'api_spend_usd': 0})
    if code: raise RuntimeError(f'{stage} exited {code}; retained log: {root / "run.log"}')
    # Wait for the stage's owned workers to leave before constructing a new engine.
    uuid = json.loads(lease.read_text())['uuid']
    for _ in range(60):
        census = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                                         '--format=csv,noheader,nounits'], text=True)
        if uuid not in census: return
        time.sleep(2)
    raise RuntimeError('stage exited but GPU workers remain; no new stage launched')


def measure_t2():
    from technical_measurements import t2
    update = json.loads((T2 / 'update/output/result.json').read_text())
    cells = json.loads(Path(json.loads((SOURCE / 'generate_refit/runtime.json').read_text())['cells_path']).read_text())
    rows = [json.loads(p.read_text()) for p in sorted((T2 / 'probabilities_refit/output').glob('*.probability.json'))]
    result = t2(update, rows, expected_cells=[c['cell_id'] for c in cells], eos_token_ids=[151643, 151645])
    from gates import single_rank_gradient
    grad = single_rank_gradient(update['metrics']['grad_norm'])
    result.update(condition='v3-A7', grad_norm=grad, reward='factored_reward', api_spend_usd=0,
                  before_parameters=update['before_parameters'], after_parameters=update['after_parameters'])
    if not math.isfinite(grad) or grad <= 0: result['status'] = 'FAIL'
    write_new(T2 / 'result.json', result)
    write_new(V3 / 'results/T2_v3.json', result)
    return result


def run(device):
    from device_guard import check
    lock = (ROOT / f'gpu_{device}.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    census = subprocess.check_output(['nvidia-smi', f'--id={device}', '--query-gpu=uuid,memory.used',
                                     '--format=csv,noheader,nounits'], text=True).strip().split(',')
    if int(census[1]) > 100: raise RuntimeError('requested GPU is not idle')
    lease = ROOT / 'phase2/technical/lease.json'
    identity = f'e13v3-T2-{os.getpid()}'
    write_new(lease, {'owner': 'e13v3', 'id': identity, 'status': 'ACTIVE', 'index': device,
                     'uuid': census[0].strip(), 'started_unix': time.time(),
                     'expires_unix': time.time() + 10 * 3600})
    os.environ.update(CUDA_VISIBLE_DEVICES=str(device), CUDA_DEVICE_ORDER='PCI_BUS_ID', E13_EXECUTION_ID=identity)
    check({'lease_path': str(lease)})
    try:
        execute('update', T2 / 'update', lease, groups_path=str(T2 / 'score/groups.json'),
                checkpoint=str(SOURCE / 'update/output/before'))
        execute('export', T2 / 'export', lease, checkpoint=str(T2 / 'update/output/after'))
        execute('generate', T2 / 'generate_refit', lease, model=str(T2 / 'export/output'))
        execute('probabilities', T2 / 'probabilities_refit', lease,
                model=str(T2 / 'export/output'), checkpoint=str(T2 / 'update/output/after'),
                generation_root=str(T2 / 'generate_refit/output'))
        result = measure_t2()
        if result['status'] != 'PASS': return
        execute('replay', T3 / 'replay', lease, source_update=str(T2 / 'update/output'))
        from technical_measurements import t3
        result = t3(json.loads((T2 / 'update/output/result.json').read_text()),
                    json.loads((T3 / 'replay/output/result.json').read_text()),
                    source_result_sha256=digest(T2 / 'update/output/result.json'))
        result.update(condition='v3-A7', api_spend_usd=0)
        write_new(T3 / 'result.json', result)
        write_new(V3 / 'results/T3_v3.json', result)
    finally:
        write_new(lease.with_name('lease_end.json'), {'ended_unix': time.time(), 'id': identity,
                  'gpu_census': subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                                                        '--format=csv,noheader,nounits'], text=True)})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run', 'measure-t2'])
    parser.add_argument('--device', type=int, choices=[0, 5, 7], default=0)
    args = parser.parse_args()
    if args.action == 'prepare': prepare()
    elif args.action == 'measure-t2': print(json.dumps(measure_t2(), sort_keys=True))
    else: run(args.device)
