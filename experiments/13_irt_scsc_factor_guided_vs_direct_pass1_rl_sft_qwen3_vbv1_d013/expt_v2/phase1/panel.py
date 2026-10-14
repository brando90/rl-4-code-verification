"""Execute a frozen train-only anchor manifest once, retaining every failed slot."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time

BATCHES = ('lp1', 'base', 'half', 'full1', 'full2')
SEEDS = dict(zip(BATCHES, (1302101, 1302111, 1302121, 1302131, 1302141)))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def write_new(path, value):
    """Exclusive durable receipt: neither restart nor another writer can erase it."""
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def cell_seed(batch, task, sample):
    if batch not in SEEDS or not 0 <= sample < 8:
        raise ValueError('unregistered batch/sample')
    key = f'e13v2-anchor\0{SEEDS[batch]}\0{task}\0{sample}'
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], 'big')


def validate_manifest(manifest, train_ids):
    batch = manifest['batch']; cells = manifest['cells']
    train = set(train_ids)
    if batch not in BATCHES or len(train_ids) != 539 or len(train) != 539:
        raise ValueError('incorrect batch or train allowlist')
    if len(cells) != (8 if batch == 'lp1' else 539 * 8):
        raise ValueError('incomplete declared panel')
    seen = set(); seeds = set()
    for cell in cells:
        task, sample = cell['task_id'], cell['sample']
        expected = f'{batch}/{task}/{sample}'
        if task not in train or cell['split'] != 'train' or cell['cell_id'] != expected:
            raise ValueError('cell is outside the declared train cohort')
        if (task, sample) in seen or cell['seed'] != cell_seed(batch, task, sample):
            raise ValueError('duplicate cell or changed seed')
        if cell['seed'] in seeds:
            raise ValueError('seed collision in declared batch')
        seen.add((task, sample)); seeds.add(cell['seed'])
        tokens = cell['prompt_token_ids']
        if not tokens or any(type(t) is not int or t < 0 for t in tokens):
            raise ValueError('invalid prompt tokens')
        if len(tokens) + 8192 > manifest['max_model_len']:
            raise ValueError('prompt would shorten frozen generation cap')
    if batch != 'lp1' and seen != {(t, s) for t in train for s in range(8)}:
        raise ValueError('anchor denominator changed')
    if batch == 'lp1':
        ranked = sorted(train, key=lambda t: hashlib.sha256(('e13v2-lp1\0' + t).encode()).hexdigest())[:8]
        if seen != {(t, 0) for t in ranked}:
            raise ValueError('probe is not the frozen outcome-blind eight tasks')
    return cells


def check_prerequisites(batch, lp1=None, calibration=None):
    if batch != 'lp1' and (not lp1 or lp1.get('status') != 'PASS'):
        raise ValueError('anchor generation requires published LP-1 PASS')
    if batch == 'full2' and (not calibration or calibration.get('status') != 'FROZEN'
                             or calibration.get('F2') != .75):
        raise ValueError('independent batch 2 requires calibration/item/F2 freeze')


def generate_once(manifest, train_ids, root, generate, *, lease_check, prerequisites):
    """Call a supplied frozen engine once per slot; no implicit retry or refill.

    `generate` returns the exact token/log-probability receipt. Infrastructure
    exceptions terminate this attempt and leave uncalled manifest slots missing.
    Scoring is separate: length-capped responses remain eligible for strict 1.
    """
    cells = validate_manifest(manifest, train_ids)
    check_prerequisites(manifest['batch'], **prerequisites)
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    lease_check()
    write_new(root / 'attempt.json', {'batch': manifest['batch'], 'started_unix': time.time(),
                                    'declared_cells': len(cells), 'retries': 0})
    completed = 0
    try:
        for index, cell in enumerate(cells):
            lease_check()
            write_new(root / f'{index:05d}.started.json', {'cell_id': cell['cell_id'], 'seed': cell['seed']})
            raw = generate(cell)
            if raw['prompt_token_ids'] != cell['prompt_token_ids']:
                raise ValueError('engine changed prompt tokens')
            output = raw['output_token_ids']
            if not output or len(output) > 8192 or len(raw['generation_logprobs']) != len(output):
                raise ValueError('invalid generation receipt')
            if raw['finish_reason'] not in ('stop', 'length'):
                raise ValueError('unmeasured finish reason')
            if raw['finish_reason'] == 'length' and len(output) != 8192:
                raise ValueError('generation used an undeclared context cap')
            if any(t in manifest['terminal_token_ids'] for t in output[:-1]):
                raise ValueError('response continued after a terminal token')
            if raw['finish_reason'] == 'stop' and output[-1] not in manifest['terminal_token_ids']:
                raise ValueError('unknown stop action')
            row = {**cell, **raw, 'cell_id': cell['cell_id'], 'split': 'train',
                   'at_token_cap': raw['finish_reason'] == 'length'}
            write_new(root / f'{index:05d}.generation.json', row)
            completed += 1
    except BaseException as exc:
        write_new(root / 'terminal.json', {'status': 'INCOMPLETE', 'completed': completed,
                  'declared': len(cells), 'error_type': type(exc).__name__, 'retries': 0})
        raise
    result = {'status': 'COMPLETE', 'completed': completed, 'declared': len(cells), 'retries': 0}
    write_new(root / 'terminal.json', result)
    return result
