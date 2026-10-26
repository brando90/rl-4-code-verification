"""Generate a fixed learning prefix, stopping only after complete eight-response groups at token boundaries."""
from __future__ import annotations

import json
import math
from pathlib import Path

from generation_core import validate_cells, sampler, build_engine, check_lease, numerical_dtype
from panel import validate_generation
from schedule import advance_group
from training_checkpoint import write_new, digest


def validate_groups(cells, state=None):
    if len(cells) != 256 or len(cells) % 8:
        raise ValueError('a scheduled learning opportunity declares 32 complete groups')
    for index in range(0, len(cells), 8):
        group = cells[index:index+8]
        if (len({r['group_index'] for r in group}) != 1 or len({r['task_id'] for r in group}) != 1
                or [r['sample'] for r in group] != list(range(8))):
            raise ValueError('learning rollout group identity changed')
        if index and group[0]['group_index'] != cells[index-8]['group_index']+1:
            raise ValueError('learning groups must be one contiguous deterministic prefix')
    for key in ('arm', 'run_seed', 'update'):
        if len({r[key] for r in cells}) != 1: raise ValueError('learning run/update identity changed')
    if state is not None:
        if state['update_groups'] != 0 or state['group_index'] != cells[0]['group_index']:
            raise ValueError('token-boundary state does not precede this scheduled prefix')
        if state['generated_tokens'] >= state['next_target']: raise ValueError('token boundary already closed')


def chunk_size(state, remaining):
    # Far from a boundary, even the maximum possible chunk cannot cross it.
    # Near a boundary generate just one whole group, never an unrequested tail.
    size = 32 if state is None or state['next_target']-state['generated_tokens'] > 32*8192 else 8
    return min(size, remaining)


def generate(config, cells, *, root, budget_state=None):
    from transformers import AutoTokenizer
    cells = validate_cells(cells, Path(config['train_ids']).read_text().splitlines())
    validate_groups(cells, budget_state)
    if numerical_dtype(config) != 'float16' or config['batch_size'] != 32:
        raise ValueError('S2 precision or engine batching changed')
    root = Path(root); root.mkdir(parents=True, exist_ok=False)
    state = dict(budget_state) if budget_state is not None else None
    contract = {'max_model_len': 15945, 'terminal_token_ids': config['terminal_token_ids']}
    write_new(root/'maximum_prefix.json', cells)
    write_new(root/'attempt.json', {'condition': 'v2-S2', 'maximum_declared_slots': 256,
        'maximum_prefix_sha256': digest(root/'maximum_prefix.json'), 'budget_state_before': state,
        'rule': 'stop after crossing complete group or 32 complete groups; all generated tokens retained',
        'automatic_retry': False})
    rows = []; offset = 0
    try:
        check_lease(config)
        tokenizer = AutoTokenizer.from_pretrained(config['tokenizer'], local_files_only=True)
        engine = build_engine(config, contract)
        while offset < len(cells):
            check_lease(config); chunk = cells[offset:offset+chunk_size(state, len(cells)-offset)]
            outputs = engine.generate([{'prompt_token_ids': c['prompt_token_ids']} for c in chunk],
                [sampler(contract['terminal_token_ids'], c['seed']) for c in chunk], use_tqdm=False)
            if len(outputs) != len(chunk): raise ValueError('learning response denominator changed')
            chunk_rows = []; failures = []
            for index, (cell, request) in enumerate(zip(chunk, outputs), start=offset):
                try:
                    if len(request.outputs) != 1: raise ValueError('learning sample multiplicity changed')
                    output = request.outputs[0]; tokens = list(output.token_ids)
                    if output.logprobs is None or len(output.logprobs) != len(tokens):
                        raise ValueError('learning selected-token probabilities missing')
                    logprobs = [float(values[token].logprob) if token in values and math.isfinite(values[token].logprob)
                        else None for token, values in zip(tokens, output.logprobs)]
                    row = {**cell, 'condition': 'v2-S2', 'prompt_token_ids': list(request.prompt_token_ids),
                        'output_token_ids': tokens, 'generation_logprobs': logprobs,
                        'finish_reason': output.finish_reason, 'at_token_cap': output.finish_reason == 'length',
                        'completion': tokenizer.decode(tokens, skip_special_tokens=False)}
                    validate_generation(cell, row, contract)
                    write_new(root/f'{index:05d}.generation.json', row); rows.append(row); chunk_rows.append(row)
                except Exception as exc:
                    write_new(root/f'{index:05d}.error.json', {'error_type': type(exc).__name__, 'error': str(exc)})
                    failures.append(type(exc).__name__)
            if failures: raise ValueError('learning generation has incomplete group evidence')
            if state is not None:
                for first in range(0, len(chunk_rows), 8):
                    state = advance_group(state, [len(r['output_token_ids']) for r in chunk_rows[first:first+8]])
                    if state['boundary_crossed'] and first+8 != len(chunk_rows):
                        raise ValueError('generation consumed a tail after its boundary')
            offset += len(chunk)
            if state is not None and state['update_due']: break
        write_new(root/'cells.json', cells[:offset])
        result = {'condition': 'v2-S2', 'status': 'COMPLETE', 'declared': offset, 'completed': len(rows),
            'maximum_declared_slots': 256, 'ungenerated_prefix_tail': 256-offset,
            'generated_tokens': sum(len(r['output_token_ids']) for r in rows),
            'budget_state_after': state, 'complete_groups': offset//8,
            'unsupported_selected_tokens': sum(v is None for r in rows for v in r['generation_logprobs']),
            'capped_responses': sum(r['at_token_cap'] for r in rows), 'optimizer_updates': 0}
        write_new(root/'result.json', result); return result
    except Exception as exc:
        write_new(root/'error.json', {'condition': 'v2-S2', 'status': 'INCOMPLETE',
            'completed_receipts': len(rows), 'generated_tokens_in_complete_receipts': sum(len(r['output_token_ids']) for r in rows),
            'unknown_tokens_not_imputed': True, 'budget_state_after_last_complete_chunk': state,
            'error_type': type(exc).__name__, 'error': str(exc), 'automatic_retry': False})
        raise
