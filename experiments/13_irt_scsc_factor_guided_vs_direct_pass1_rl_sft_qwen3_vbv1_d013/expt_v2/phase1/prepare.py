"""Prepare private train-only prompt/token manifests without loading model weights."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from panel import BATCHES, cell_seed, validate_manifest, write_new, digest


def prepare(*, train_path, pack, veribench, model, root):
    from transformers import AutoTokenizer
    from rl4cv.veribench.pack import load_pack, read_task_ids
    from rl4cv.veribench.exp103 import build_prompt
    train = read_task_ids(train_path)
    if len(train) != 539 or len(set(train)) != 539:
        raise ValueError('train allowlist is not 539 unique tasks')
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
    terminal = sorted({tokenizer.eos_token_id, tokenizer.convert_tokens_to_ids('<|im_end|>')})
    if any(t is None or t < 0 for t in terminal):
        raise ValueError('unresolved terminal token')
    if tokenizer.convert_ids_to_tokens(tokenizer.convert_tokens_to_ids('<|im_end|>')) != '<|im_end|>':
        raise ValueError('extra stop token is not a tokenizer token')
    tasks = load_pack(pack, train)  # Never enumerate or load sealed test prompts.
    templates = {}; prompts = {}
    for task in tasks:
        prompt = build_prompt(task.instruction, root=veribench)
        token_ids = tokenizer.apply_chat_template(prompt.messages(), tokenize=True,
                                                 add_generation_prompt=True, enable_thinking=True)
        prompts[task.task_id] = {'prompt_token_ids': token_ids,
            'required_paths': list(prompt.required_paths), 'prompt_sha256': prompt.prompt_sha256,
            'system_prompt_sha256': prompt.system_prompt_sha256,
            'instruction_sha256': prompt.instruction_sha256, 'addendum_sha256': prompt.addendum_sha256}
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    max_prompt = max(len(p['prompt_token_ids']) for p in prompts.values())
    max_model_len = 8192 + max_prompt
    if max_model_len > 32768:
        raise ValueError('declared prompt plus output exceeds model context')
    ranked = sorted(train, key=lambda t: hashlib.sha256(('e13v2-lp1\0'+t).encode()).hexdigest())[:8]
    for batch in BATCHES:
        chosen = ranked if batch == 'lp1' else train
        manifest = {'batch': batch, 'max_model_len': max_model_len,
                    'terminal_token_ids': terminal, 'chat_template_kwargs': {'enable_thinking': True},
                    'train_allowlist_sha256': digest(train_path), 'cells': [
                        {'cell_id': f'{batch}/{task}/{sample}', 'task_id': task, 'sample': sample,
                         'split': 'train', 'seed': cell_seed(batch, task, sample), **prompts[task]}
                        for task in chosen for sample in (range(1) if batch == 'lp1' else range(8))]}
        validate_manifest(manifest, train)
        write_new(root / f'{batch}.manifest.json', manifest)
        templates[batch] = {'sha256': digest(root / f'{batch}.manifest.json'), 'cells': len(manifest['cells'])}
    write_new(root / 'template.json', {'chat_template': tokenizer.chat_template,
                                      'kwargs': {'enable_thinking': True, 'add_generation_prompt': True}})
    summary = {'status': 'PREPARED_NOT_EXECUTED', 'train_tasks': len(train),
               'max_prompt_tokens': max_prompt, 'max_model_len': max_model_len,
               'max_new_tokens': 8192, 'terminal_token_ids': terminal,
               'template_sha256': digest(root / 'template.json'), 'manifests': templates}
    write_new(root / 'preparation.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('train-path', 'pack', 'veribench', 'model', 'root'):
        parser.add_argument('--'+arg, type=Path, required=True)
    print(json.dumps(prepare(**vars(parser.parse_args())), indent=2))


if __name__ == '__main__':
    main()
