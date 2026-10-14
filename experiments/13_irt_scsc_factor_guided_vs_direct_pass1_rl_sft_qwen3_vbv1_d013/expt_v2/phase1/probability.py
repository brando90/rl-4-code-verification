"""Admission on actual generator/trainer token receipts, without any model calls.

The caller must use the frozen trainer's get_logprobs path and supply unchanged
token IDs. Prompt positions are excluded; every generated token, including EOS,
is included. A structural error fails the attempt, never drops a response.
"""
from __future__ import annotations

import math
import numpy as np


def assess_probability(rows: list[dict], *, eos_token_ids: list[int],
                       max_new_tokens: int = 8192) -> dict:
    if not rows or max_new_tokens != 8192 or not eos_token_ids:
        raise ValueError('empty probe or unfrozen token contract')
    seen = set()
    generation, trainer = [], []
    prompt_tokens = cap_finishes = eos_tokens = 0
    for row in rows:
        cell = row['cell_id']
        if cell in seen or row['split'] != 'train':
            raise ValueError('duplicate or nontrain probe cell')
        seen.add(cell)
        prompt, output = row['prompt_token_ids'], row['output_token_ids']
        if not prompt or not output or len(output) > max_new_tokens:
            raise ValueError('empty prompt/output or token cap exceeded')
        if any(type(x) is not int or x < 0 for x in prompt + output):
            raise ValueError('invalid token identity')
        full = prompt + output
        expected_mask = [0] * len(prompt) + [1] * len(output)
        if row['trainer_input_ids'] != full or row['trainer_token_mask'] != expected_mask:
            raise ValueError('trainer IDs or assistant mask do not match generation')
        if any(x in eos_token_ids for x in output[:-1]):
            raise ValueError('output continues after EOS')
        ended_eos = output[-1] in eos_token_ids
        finish = row['finish_reason']
        if finish == 'length':
            if len(output) != max_new_tokens:
                raise ValueError('context cap silently shortened new-token cap')
            cap_finishes += 1
        elif finish == 'stop':
            if not ended_eos:
                raise ValueError('unregistered stop token/string')
        else:
            raise ValueError('missing or unknown finish reason')
        eos_tokens += int(ended_eos)
        g = np.asarray(row['generation_logprobs'], dtype=float)
        t = np.asarray(row['trainer_logprobs'], dtype=float)
        if g.shape != (len(output),) or t.shape != (len(full),):
            raise ValueError('logprob token alignment mismatch')
        t = t[len(prompt):]
        if np.any(g[np.isfinite(g)] > 1e-6) or np.any(t[np.isfinite(t)] > 1e-6):
            raise ValueError('positive log probability')
        generation.extend(g.tolist()); trainer.extend(t.tolist())
        prompt_tokens += len(prompt)
    g, t = np.asarray(generation), np.asarray(trainer)
    supported = np.isfinite(g) & np.isfinite(t)
    unsupported = int((~supported).sum())
    error = np.abs(t[supported] - g[supported])
    median = float(np.median(error)) if len(error) else None
    p99 = float(np.quantile(error, .99, method='linear')) if len(error) else None
    # Same frozen-policy importance ratio used at the behavior/trainer boundary.
    # Compare in log space to avoid overflow; unknown support is an independent FAIL.
    truncated = int(np.sum(t[supported] - g[supported] > math.log(2.)))
    fraction = truncated / len(g)
    passed = (unsupported == 0 and median is not None and median <= .01
              and p99 <= .10 and fraction <= .01)
    return {'status': 'PASS' if passed else 'FAIL', 'responses': len(rows),
            'prompt_tokens': prompt_tokens, 'generated_tokens': len(g),
            'supported_tokens': int(supported.sum()), 'unsupported_tokens': unsupported,
            'median_absolute_logprob_error': median,
            'p99_absolute_logprob_error': p99, 'importance_ratio_cap': 2.,
            'importance_truncated_tokens': truncated,
            'importance_truncation_fraction': fraction,
            'token_cap_finishes': cap_finishes, 'eos_tokens_in_mask': eos_tokens,
            'threshold_source': 'PROTOCOL sections 5 and 6; PLAN section 5 LP-1',
            'quantile_method': 'linear',
            'interpretation': 'Technical fixed-probe admission; p-val=n/a; no optimizer update'}
