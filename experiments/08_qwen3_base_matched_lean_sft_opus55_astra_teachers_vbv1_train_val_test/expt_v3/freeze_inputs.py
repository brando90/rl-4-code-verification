"""Verify admitted bytes and prepare deterministic continuation schedules and configs."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e08')
SIZES = {'1p7b': '1.7B', '4b': '4B', '8b': '8B', '14b': '14B'}
BUDGET = 5752936


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, sort_keys=True) + '\n'
    if path.exists() and path.read_text() != text:
        raise ValueError(f'Refusing to replace differing frozen input: {path}')
    path.write_text(text)


def main():
    stats = json.loads((HERE / 'results/admitted_corpus_stats.json').read_text())
    corpus = Path(stats['files']['corpus_host_only'])
    assert sha(corpus) == stats['files']['corpus_sha256']
    assert sha(HERE / 'results/admitted_corpus_manifest.csv') == stats['files']['manifest_sha256']
    assert sha(WORK / 'sft/s_v1.jsonl') == stats['inputs']['s_v1_sha256']
    rows = [json.loads(line) for line in corpus.read_text().splitlines()]
    manifest = list(csv.DictReader((HERE / 'results/admitted_corpus_manifest.csv').open()))
    admitted = {r['example_id']: r for r in manifest if r['admitted'] == '1'}
    assert len(rows) == len(admitted) == 2585
    assert len({r['example_id'] for r in rows}) == len(rows)
    for row in rows:
        key = 'rl4cv-e08-v3-sft-order-v1:' + '|'.join(str(row[k]) for k in ('source', 'task_id', 'teacher', 'sample'))
        assert hashlib.sha256(key.encode()).hexdigest() == row['order_key']
        for k in ('source', 'task_id', 'teacher', 'sample', 'n_prompt_tokens', 'n_assistant_tokens', 'order_key'):
            assert str(row[k]) == admitted[row['example_id']][k], (row['example_id'], k)
    original = [json.loads(line) for line in (WORK / 'sft/s_v1.jsonl').read_text().splitlines()]
    for row in rows:
        if row['source'] == 'v1_selected':
            assert row['messages'] == original[row['provenance']['v1_index']]['messages']
    schedules = {}
    for condition in ('R', 'E'):
        selected = sorted([r for r in rows if condition == 'E' or r['source'] == 'v1_selected'], key=lambda r: r['order_key'])
        steps, cumulative, processed = [], 0, 0
        for offset in range(0, len(selected), 2):
            batch = selected[offset:offset + 2]
            loss = sum(r['n_assistant_tokens'] + 1 for r in batch)
            prompt = sum(r['n_prompt_tokens'] for r in batch)
            cumulative += loss
            processed += loss + prompt
            steps.append({'step': len(steps) + 1, 'example_ids': [r['example_id'] for r in batch],
                          'loss_tokens': loss, 'prompt_tokens': prompt,
                          'cumulative_loss_tokens': cumulative, 'cumulative_processed_tokens': processed,
                          'padding_slots': 2 - len(batch)})
            if cumulative >= BUDGET:
                break
        assert cumulative >= BUDGET
        checkpoints = {}
        for label, target in [('f0p5', BUDGET // 2), ('f1p0', BUDGET)]:
            step = next(s for s in steps if s['cumulative_loss_tokens'] >= target)
            consumed = selected[:step['step'] * 2]
            checkpoints[label] = {**step, 'target_loss_tokens': target,
                                  'overshoot_tokens': step['cumulative_loss_tokens'] - target,
                                  'source_counts': dict(Counter(r['source'] for r in consumed))}
        nsteps = len(steps)
        warmup = math.ceil(.03 * nsteps)
        out = WORK / f'sft_v3/s_v3_{condition}_nemo.jsonl'
        examples = [{'messages': r['messages'], 'example_id': r['example_id'], 'is_padding': False} for r in selected]
        if len(examples) % 2:
            examples.append({'messages': [{'role': 'system', 'content': 'padding slot'},
                                          {'role': 'user', 'content': ('<pad> ' * (16384 + 64)).strip()},
                                          {'role': 'assistant', 'content': 'padding slot'}], 'is_padding': True})
        out.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in examples))
        dummy = out.with_name(f's_v3_{condition}_val_dummy.jsonl')
        dummy.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in examples[:2]))
        schedule = {'condition': condition, 'corpus_sha256': sha(corpus), 'manifest_sha256': stats['files']['manifest_sha256'],
                    'n_pool_examples': len(selected), 'global_batch': 2, 'budget_loss_tokens': BUDGET,
                    'planned_steps': nsteps, 'warmup_steps': warmup, 'cosine_T_max': nsteps - warmup,
                    'nemo_jsonl': str(out), 'nemo_jsonl_sha256': sha(out), 'val_dummy': str(dummy),
                    'loss_span': 'rendered assistant span plus one endoftext token',
                    'steps': steps, 'checkpoints': checkpoints}
        if condition == 'R':
            assert nsteps == 658 and cumulative == BUDGET
        write(HERE / f'results/sft_schedule_v3_{condition}.json', schedule)
        schedules[condition] = schedule
        for size in SIZES.values():
            config = yaml.safe_load((HERE.parent / f'expt_v1/configs/e08_sft_{size}.yaml').read_text())
            config['sft']['max_num_steps'] = nsteps
            config['policy']['scheduler'][0]['kwargs'].update(start_factor=1 / warmup, total_iters=warmup)
            config['policy']['scheduler'][1]['kwargs']['T_max'] = nsteps - warmup
            config['policy']['scheduler'][2]['milestones'] = [warmup]
            path = HERE / f'configs/e08_v3_{condition}_{size}.yaml'
            path.parent.mkdir(exist_ok=True)
            path.write_text('# TLDR: Matched continuation; weights-only step-658 start and fresh optimizer.\n' + yaml.safe_dump(config, sort_keys=False))
        print(condition, nsteps, checkpoints)
    v1 = json.loads((HERE.parent / 'expt_v1/results/ladder_manifest.json').read_text())
    task_file = HERE.parent / 'expt_v1/results/split/vbv1_validation_task_ids.txt'
    tasks = task_file.read_text().splitlines()
    assert len(tasks) == len(set(tasks)) == 135 and sha(task_file) == v1['task_ids_sha256']
    systems = []
    for condition in ('R', 'E'):
        for short, size in SIZES.items():
            start = next(r for r in v1['systems'] if r['size'] == size and r.get('step') == 658)
            assert sha(Path(start['hf_path']) / 'SHA256SUMS') == start['weights_sha256_manifest']
            for fraction in ('f0p5', 'f1p0'):
                ckpt = schedules[condition]['checkpoints'][fraction]
                systems.append({'label': f'v3_{condition}_{short}_{fraction}', 'condition': condition, 'size': size,
                                'fraction': fraction, 'step': ckpt['step'], 'loss_tokens': ckpt['cumulative_loss_tokens'],
                                'start_hf_path': start['hf_path'], 'start_weights_sha256_manifest': start['weights_sha256_manifest'],
                                'hf_path': str(WORK / f'sft_v3/ckpt/v3_{condition}_{short}/hf/step_{ckpt["step"]}')})
    write(HERE / 'results/ladder_manifest_v3.json', {'split': 'validation', 'n_tasks': 135, 'samples_per_task': 8,
          'n_systems': 16, 'n_declared_cells': 17280, 'task_ids': tasks, 'task_ids_sha256': sha(task_file),
          'sampling': v1['sampling'], 'systems': systems,
          'cells': [{'system': s['label'], 'task_id': tid, 'sample_idx': sample} for s in systems for tid in tasks for sample in range(8)]})


if __name__ == '__main__':
    main()
