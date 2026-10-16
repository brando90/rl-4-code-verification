"""Reconcile actual TensorBoard loss-token steps with a frozen continuation schedule."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3')
sys.path.insert(0, str(HERE.parent / 'expt_v1/scripts'))
from extract_train_logs_e08 import load_scalars


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('condition', choices=['R', 'E'])
    parser.add_argument('size', choices=['1p7b', '4b', '8b', '14b'])
    parser.add_argument('--dry', action='store_true')
    args = parser.parse_args()
    schedule = json.loads((HERE / f'results/sft_schedule_v3_{args.condition}.json').read_text())
    label = f'v3_{args.condition}_{args.size}'
    root = WORK / ('dry_run' if args.dry else f'ckpt/{label}')
    scalars = load_scalars(root / 'logs')
    tokens = scalars.get('train/global_valid_toks', {})
    expected = schedule['steps'][:8] if args.dry else schedule['steps']
    assert sorted(tokens) == list(range(1, len(expected) + 1)), (sorted(tokens), len(expected))
    rows = []
    for step in expected:
        i = step['step']
        assert int(tokens[i]) == step['loss_tokens'], (i, tokens[i], step['loss_tokens'])
        rows.append({'step': i, 'loss': scalars['train/loss'][i], 'lr': scalars['train/lr'][i],
                     'loss_tokens': int(tokens[i]), 'cumulative_loss_tokens': step['cumulative_loss_tokens'],
                     'processed_tokens': step['prompt_tokens'] + step['loss_tokens'],
                     'step_wall_seconds': scalars.get('timing/train/total_step_time', {}).get(i)})
    out = HERE / 'results/train_logs'
    out.mkdir(exist_ok=True)
    name = 'dry_run' if args.dry else label
    with (out / f'{name}_steps.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    receipt = {'status': 'PASS', 'steps': len(rows), 'loss_tokens': sum(r['loss_tokens'] for r in rows),
               'schedule_sha256': hashlib.sha256((HERE / f'results/sft_schedule_v3_{args.condition}.json').read_bytes()).hexdigest(),
               'token_counts_match': True, 'scalar_tags': sorted(scalars)}
    receipt['training_step_wall_seconds'] = sum(r['step_wall_seconds'] or 0 for r in rows)
    receipt['processed_real_tokens'] = sum(r['processed_tokens'] for r in rows)
    if args.dry:
        val = scalars.get('validation/val_loss', {})
        assert len(val) >= 2, scalars.keys()
        before, after = val[min(val)], val[max(val)]
        assert after < before, (before, after)
        receipt['fixed_set_eval_loss'] = {'before': before, 'after': after}
        generated = [json.loads(l) for l in (root / 'gen_preflight.jsonl').read_text().splitlines()]
        assert len(generated) == 2 and len({r['task_id'] for r in generated}) == 2
        receipt['generation'] = [{k: r.get(k) for k in ('task_id', 'sample_idx', 'extraction', 'generated_tokens', 'finish_reason')} for r in generated]
        assert any(r.get('extraction') not in (None, 'no_lean_block') for r in generated)
        receipt['export_sha256_manifest'] = hashlib.sha256((root / 'hf/step_8/SHA256SUMS').read_bytes()).hexdigest()
        path = HERE / 'results/dry_run_v3.json'
    else:
        path = out / f'{label}_summary.json'
    path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
