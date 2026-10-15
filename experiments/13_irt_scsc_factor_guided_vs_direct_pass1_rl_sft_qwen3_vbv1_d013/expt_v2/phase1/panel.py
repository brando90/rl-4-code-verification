"""Execute a frozen train-only anchor manifest once, retaining every failed slot."""
from __future__ import annotations

import hashlib
import json
import os
import random
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


def development_tasks(train_ids):
    """Seeded outcome-blind train draw disjoint from the unchanged LP-1 tasks."""
    original = set(sorted(train_ids, key=lambda t: hashlib.sha256(
        ('e13v2-lp1\0' + t).encode()).hexdigest())[:8])
    return random.Random(1302151).sample(sorted(set(train_ids) - original), 8)


def validate_manifest(manifest, train_ids):
    batch = manifest['batch']; cells = manifest['cells']
    development = batch == 'lp1_a5_dev'
    probe = batch == 'lp1' or development
    train = set(train_ids)
    if (batch not in BATCHES and not development) or len(train_ids) != 539 or len(train) != 539:
        raise ValueError('incorrect batch or train allowlist')
    if len(cells) != (8 if probe else 539 * 8):
        raise ValueError('incomplete declared panel')
    seen = set(); seeds = set()
    for cell in cells:
        task, sample = cell['task_id'], cell['sample']
        expected = f'{batch}/{task}/{sample}'
        if task not in train or cell['split'] != 'train' or cell['cell_id'] != expected:
            raise ValueError('cell is outside the declared train cohort')
        if (task, sample) in seen or cell['seed'] != cell_seed('lp1' if development else batch, task, sample):
            raise ValueError('duplicate cell or changed seed')
        if cell['seed'] in seeds:
            raise ValueError('seed collision in declared batch')
        seen.add((task, sample)); seeds.add(cell['seed'])
        tokens = cell['prompt_token_ids']
        if not tokens or any(type(t) is not int or t < 0 for t in tokens):
            raise ValueError('invalid prompt tokens')
        if len(tokens) + 8192 > manifest['max_model_len']:
            raise ValueError('prompt would shorten frozen generation cap')
    if not probe and seen != {(t, s) for t in train for s in range(8)}:
        raise ValueError('anchor denominator changed')
    if development:
        if seen != {(t, 0) for t in development_tasks(train_ids)}:
            raise ValueError('changed or overlapping A5 development probe')
    if batch == 'lp1':
        ranked = sorted(train, key=lambda t: hashlib.sha256(('e13v2-lp1\0' + t).encode()).hexdigest())[:8]
        if seen != {(t, 0) for t in ranked}:
            raise ValueError('probe is not the frozen outcome-blind eight tasks')
    return cells


def check_prerequisites(batch, lp1=None, calibration=None):
    if batch not in ('lp1', 'lp1_a5_dev') and (not lp1 or lp1.get('status') != 'PASS'):
        raise ValueError('anchor generation requires published LP-1 PASS')
    if batch == 'full2' and (not calibration or calibration.get('status') != 'FROZEN'
                             or calibration.get('F2') != .75):
        raise ValueError('independent batch 2 requires calibration/item/F2 freeze')


def generate_once(manifest, train_ids, root, generate, *, lease_check, prerequisites,
                  batch_size=1, generate_batch=None):
    """Call a supplied frozen engine once per slot; no implicit retry or refill.

    `generate` returns the exact token/log-probability receipt. Infrastructure
    exceptions terminate this attempt and leave uncalled manifest slots missing.
    Scoring is separate: length-capped responses remain eligible for strict 1.
    """
    cells = validate_manifest(manifest, train_ids)
    if type(batch_size) is not int or not 1 <= batch_size <= 32:
        raise ValueError('batch size outside declared resource envelope')
    if batch_size != 1 and generate_batch is None:
        raise ValueError('batched generation requires a batch engine')
    check_prerequisites(manifest['batch'], **prerequisites)
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    lease_check()
    write_new(root / 'attempt.json', {'batch': manifest['batch'], 'started_unix': time.time(),
                                    'declared_cells': len(cells), 'retries': 0})
    completed = 0
    try:
        for offset in range(0, len(cells), batch_size):
            lease_check()
            chunk = cells[offset:offset+batch_size]
            for index, cell in enumerate(chunk, start=offset):
                write_new(root / f'{index:05d}.started.json', {'cell_id': cell['cell_id'], 'seed': cell['seed']})
            raws = generate_batch(chunk) if generate_batch else [generate(chunk[0])]
            # Preserve the entire returned batch even if one receipt is malformed.
            write_new(root / f'batch_{offset:05d}.raw.json', raws)
            if len(raws) != len(chunk):
                raise ValueError('batch engine omitted or added a response')
            for index, (cell, raw) in enumerate(zip(chunk, raws), start=offset):
                validate_generation(cell, raw, manifest)
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


def validate_generation(cell, raw, manifest):
    """Check one unchanged token receipt without using its scorer outcome."""
    if raw['prompt_token_ids'] != cell['prompt_token_ids']:
        raise ValueError('engine changed prompt tokens')
    output = raw['output_token_ids']
    if not output or len(output) > 8192 or len(raw['generation_logprobs']) != len(output):
        raise ValueError('invalid generation receipt')
    if any(type(token) is not int or token < 0 for token in output):
        raise ValueError('invalid generated token identity')
    if raw['finish_reason'] not in ('stop', 'length'):
        raise ValueError('unmeasured finish reason')
    if raw['finish_reason'] == 'length' and len(output) != 8192:
        raise ValueError('generation used an undeclared context cap')
    if any(t in manifest['terminal_token_ids'] for t in output[:-1]):
        raise ValueError('response continued after a terminal token')
    if raw['finish_reason'] == 'stop' and output[-1] not in manifest['terminal_token_ids']:
        raise ValueError('unknown stop action')
