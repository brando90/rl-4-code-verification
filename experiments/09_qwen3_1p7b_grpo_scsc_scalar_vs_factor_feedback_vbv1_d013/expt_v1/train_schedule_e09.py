"""TLDR: All-539-task cyclic schedule and train-only context bound before any measurement."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random


SEEDS = (20261008, 20261009)
EXPERIMENT = Path(__file__).resolve().parent
REPO = EXPERIMENT.parents[2]
SPLIT = REPO / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/vbv1_train_task_ids.txt'
PACK = Path('/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896')


def schedule(ids: list[str], seed: int, count: int):
    if len(ids) != 539 or len(set(ids)) != 539:
        raise ValueError('Expected the exact 539-task training split')
    if seed not in SEEDS or count < 0:
        raise ValueError('Undeclared seed or count')
    shuffled = list(ids)
    random.Random(seed).shuffle(shuffled)
    # Select cyclically before batching; all 539 remain reachable. Do not pass
    # a bare 539-row loader with drop_last and drop the final three every epoch.
    return [{'schedule_index': i, 'task_id': shuffled[i % 539], 'seed': seed} for i in range(count)]


def context_audit():
    from transformers import AutoTokenizer
    from rl4cv.veribench.exp103 import build_prompt
    from prompts_e09 import initial_messages, COMPLETION_REMINDER
    from two_turn_env import MeasuredAnswer, render_feedback, qwen_continuation
    from rl4cv.rewards import ScoredResponse
    tokenizer = AutoTokenizer.from_pretrained('/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/1.7B/hf/step_658', local_files_only=True)
    ids = SPLIT.read_text().splitlines()
    assert len(ids) == 539
    rows = []
    for task_id in ids:
        prompt = build_prompt((PACK / task_id / 'instruction.md').read_text(), root=REPO / 'external/veribench')
        tokens = tokenizer.apply_chat_template(initial_messages(prompt), tokenize=True,
                                               add_generation_prompt=True, enable_thinking=False)
        rows.append({'task_id': task_id, 'prompt_tokens': len(tokens), 'prompt_sha256': prompt.prompt_sha256})
    # Compiler feedback is limited to 2000 Unicode characters by the environment.
    # Conservative UTF-8 byte/token bound: at most four bytes per character,
    # and at most one token per byte, plus measured fixed template overhead.
    fixture = MeasuredAnswer(ScoredResponse(True, True, 1, 1, 1, .5), '', 'measured')
    fixed_feedback = len(tokenizer.encode(qwen_continuation(tokenizer, render_feedback('C', fixture), False), add_special_tokens=False))
    conservative_feedback = fixed_feedback + 8000
    max_prompt = max(row['prompt_tokens'] for row in rows)
    result = {'train_tasks': len(rows), 'split_sha256': hashlib.sha256(SPLIT.read_bytes()).hexdigest(),
              'rows': rows, 'max_prompt_tokens': max_prompt, 'fixed_feedback_tokens': fixed_feedback,
              'conservative_feedback_tokens': conservative_feedback,
              'required_context_bound': max_prompt + 2 * 8192 + conservative_feedback,
              'completion_reminder_sha256': hashlib.sha256(COMPLETION_REMINDER.encode()).hexdigest(),
              'note': 'Training inputs only; a Unicode-byte feedback bound, not observed rollout lengths.'}
    out = REPO.parent / 'receipts/train_context_audit.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)


if __name__ == '__main__':
    context_audit()
