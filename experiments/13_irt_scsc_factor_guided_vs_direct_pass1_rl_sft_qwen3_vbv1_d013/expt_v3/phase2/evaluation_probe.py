"""Measure the frozen eight-cell train evaluation cost after v3 T2 and T3 pass, entirely offline."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

from technical import ROOT, V3, SOURCE, execute
from cohort import digest
from training_checkpoint import write_new
from costs import snapshot, difference

T4 = ROOT / 'phase2/technical/T4/attempt_1'
PREPARATION = SOURCE.parents[2] / 'technical_preparation'


def require_gates():
    for name in ('T2', 'T3'):
        path = ROOT / f'phase2/technical/{name}/attempt_1/result.json'
        result = json.loads(path.read_text())
        if result['condition'] != 'v3-A7' or result['status'] != 'PASS':
            raise ValueError('T4 requires both preceding v3 gates to pass')


def run(device):
    require_gates()
    manifest_path = PREPARATION / 'inputs_v1/evaluation_probe.json'
    if digest(manifest_path) != '91fe553dd3a898c7f768873e694d2873bb462f44124d78758ea1996d66c49ea4':
        raise ValueError('frozen train-only evaluation probe changed')
    manifest = json.loads(manifest_path.read_text())
    T4.mkdir(parents=True, exist_ok=False)
    write_new(T4 / 'manifest.json', manifest)
    lock = (ROOT / f'gpu_{device}.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    uuid, memory = subprocess.check_output(['nvidia-smi', f'--id={device}',
        '--query-gpu=uuid,memory.used', '--format=csv,noheader,nounits'], text=True).strip().split(',')
    if int(memory) > 100: raise RuntimeError('requested GPU is not idle')
    identity = f'e13v3-T4-{os.getpid()}'
    lease = T4 / 'lease.json'
    started = time.time()
    write_new(lease, {'owner': 'e13v3', 'id': identity, 'index': device, 'uuid': uuid.strip(),
                     'status': 'ACTIVE', 'started_unix': started, 'expires_unix': started + 3600})
    os.environ.update(CUDA_VISIBLE_DEVICES=str(device), CUDA_DEVICE_ORDER='PCI_BUS_ID', E13_EXECUTION_ID=identity)
    before = snapshot(T4)
    execute('evaluation_generate', T4 / 'evaluation_generate', lease, manifest=str(T4 / 'manifest.json'),
            allowlist=str(SOURCE.parents[3] / 'phase1/train_ids.txt'), max_model_len=32768)
    generation_cost = difference(before, snapshot(T4))
    generation_cost['device_hours'] = (time.time() - started) / 3600
    write_new(T4 / 'generation_cost.json', generation_cost)
    write_new(T4 / 'lease_end.json', {'id': identity, 'ended_unix': time.time(),
                                    'device_hours': generation_cost['device_hours'], 'status': 'RELEASED'})
    fcntl.flock(lock, fcntl.LOCK_UN)
    # CPU scoring never needs to reserve a GPU.
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    from score_evaluation import score_manifest
    config = json.loads((PREPARATION / 'configuration_A6_S2_T2_A4_OBSERVATION.json').read_text())
    scoring = {**config['scoring'], 'root': str(T4 / 'evaluation_score'), 'purpose': 'T4_train_cost',
               'split': 'train', 'allowlist': str(SOURCE.parents[3] / 'phase1/train_ids.txt'),
               'controller_fence': str(T4 / 'scoring.lock')}
    generated = T4 / 'evaluation_generate/output'
    refs = {c['cell_id']: {'path': str(generated / f'{i:05d}.generation.json'),
                          'sha256': digest(generated / f'{i:05d}.generation.json')}
            for i, c in enumerate(manifest['cells'])}
    before = snapshot(T4)
    scores = score_manifest(manifest, scoring, refs, digest(T4 / 'manifest.json'))
    scoring_cost = difference(before, snapshot(T4))
    write_new(T4 / 'scoring_cost.json', scoring_cost)
    result = {'condition': 'v3-A7', 'gate': 'T4', 'status': 'COST_PROBE_MEASURED',
              'declared': 8, 'measured': scores['measured'], 'api_spend_usd': 0,
              'generation_cost': generation_cost, 'scoring_cost': scoring_cost,
              'projection_status': 'PENDING_FULL_RESOURCE_PROJECTION',
              'learning_admitted': False, 'source_manifest_sha256': digest(manifest_path)}
    write_new(T4 / 'result.json', result)
    write_new(V3 / 'results/T4_v3_probe.json', result)
    write_new(V3 / 'results/T4_v3_scores.json', scores)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', type=int, choices=[0, 5, 7], default=0)
    args = parser.parse_args()
    print(json.dumps(run(args.device), sort_keys=True))
