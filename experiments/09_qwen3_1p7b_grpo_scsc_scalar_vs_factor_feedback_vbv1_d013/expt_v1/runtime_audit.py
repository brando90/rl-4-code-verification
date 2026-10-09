"""TLDR: Durable fail-closed checks on the actual NeMo rollout and optimizer path."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random

import numpy as np
import torch


def root():
    return Path(os.environ['E09_CONTROL_DIR'])


def json_receipt(name, data):
    target = root() / name
    tmp = target.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    tmp.replace(target)


def record_batch(batch, train_data, tokenizer, step):
    expected = torch.zeros_like(train_data['token_mask'])
    assistant_count = 0
    for i, messages in enumerate(batch['message_log']):
        cursor = 0
        assert [m['role'] for m in messages] == ['user', 'assistant', 'user', 'assistant', 'user']
        assert batch['extra_env_info'][i]['turn'] == 2
        assert batch['extra_env_info'][i]['final_response'] == messages[3]['content']
        assert not batch['truncated'][i]
        assert batch['total_reward'][i] == batch['extra_env_info'][i]['final_reward']
        for message in messages:
            n = len(message['token_ids'])
            assert torch.equal(train_data['input_ids'][i, cursor:cursor+n], message['token_ids'])
            if message['role'] == 'assistant':
                expected[i, cursor:cursor+n] = 1
                assistant_count += n
            else:
                encoded = torch.tensor(tokenizer.encode(message['content'], add_special_tokens=False), dtype=torch.long)
                assert torch.equal(encoded, message['token_ids'])
            cursor += n
    assert torch.equal(expected, train_data['token_mask']), 'Prompt/feedback leak or omitted assistant actions'
    assert torch.all(train_data['sample_mask'] == 1)
    assert int(expected[:, 1:].sum()) == assistant_count
    torch.save({'rollout': batch, 'train_data': train_data}, root() / f'batch_{step}.pt')
    json_receipt(f'batch_{step}_audit.json', {'status': 'PASS', 'trajectories': len(expected),
                 'assistant_tokens': assistant_count, 'both_assistant_spans': True,
                 'prompt_feedback_loss_tokens': 0, 'terminal_metadata_retained': True})


def tensor_sample(value):
    if hasattr(value, 'to_local'):
        value = value.to_local()
    return value.detach().reshape(-1)[:128].cpu().contiguous().view(torch.uint8).numpy().tobytes()


def sample_digest(model, optimizer=None):
    """Explicitly a deterministic sample digest, NOT an endpoint identity hash."""
    h = hashlib.sha256()
    for name, parameter in model.named_parameters():
        h.update(name.encode())
        h.update(tensor_sample(parameter))
    if optimizer is not None:
        for state in optimizer.state.values():
            for key in sorted(state):
                h.update(key.encode())
                val = state[key]
                h.update(tensor_sample(val) if torch.is_tensor(val) else repr(val).encode())
    return h.hexdigest()


def rng_state():
    return {'python': random.getstate(), 'numpy': np.random.get_state(),
            'torch': torch.get_rng_state(), 'cuda': torch.cuda.get_rng_state_all()}


def restore_rng(state):
    random.setstate(state['python'])
    np.random.set_state(state['numpy'])
    torch.set_rng_state(state['torch'])
    torch.cuda.set_rng_state_all(state['cuda'])


def before_step(worker, global_batches):
    assert global_batches == 1, 'More than one optimizer update per fresh rollout batch'
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in worker.model.parameters())
    worker._e09_before_digest = sample_digest(worker.model)
    worker._e09_steps = getattr(worker, '_e09_steps', 0)


def after_step(worker):
    worker._e09_steps += 1
    digest = sample_digest(worker.model)
    assert digest != worker._e09_before_digest, 'Disposable control did not change model weights'
    json_receipt('optimizer_step.json', {'optimizer_steps': worker._e09_steps,
                 'finite_gradients': True, 'weights_changed': True,
                 'before_parameter_sample_sha256': worker._e09_before_digest,
                 'after_parameter_sample_sha256': digest})


def save_rng_and_verify_reload(worker, weights_path, optimizer_path):
    """At the one disposable save only, reload actual saved weights/Adam/scheduler.

    Compare parameter+optimizer samples and scheduler, and restore full RNG.
    Intentionally perturb a sampled weight/moment before load to expose a no-op.
    """
    state = rng_state()
    torch.save(state, Path(optimizer_path) / 'e09_rng.pt')
    expected = sample_digest(worker.model, worker.optimizer)
    scheduler = worker.scheduler.state_dict()
    with torch.no_grad():
        first = next(worker.model.parameters())
        first.add_(1)
        for slot in worker.optimizer.state.values():
            if 'exp_avg' in slot:
                slot['exp_avg'].add_(1)
                break
    assert sample_digest(worker.model, worker.optimizer) != expected
    worker.load_checkpoint(weights_path, optimizer_path)
    actual = sample_digest(worker.model, worker.optimizer)
    assert actual == expected, 'Weights/optimizer failed the save-reload control'
    assert worker.scheduler.state_dict() == scheduler
    restore_rng(torch.load(Path(optimizer_path) / 'e09_rng.pt', weights_only=False))
    assert torch.equal(torch.get_rng_state(), state['torch'])
    assert all(torch.equal(a, b) for a, b in zip(torch.cuda.get_rng_state_all(), state['cuda']))
    json_receipt('save_reload.json', {'status': 'PASS', 'sample_digest': actual,
                 'weights_and_optimizer_perturbed_then_reloaded': True,
                 'scheduler_restored': True, 'full_rng_restored': True,
                 'optimizer_steps': worker._e09_steps})
    full_context_capacity(worker)


def full_context_capacity(worker):
    """Synthetic full-length forward/backward allocation; no second optimizer step."""
    from filtered_policy import selected_logprobs
    assert not worker.enable_seq_packing and worker.cp_size == 1
    size = worker.cfg['max_total_sequence_length']
    assert size >= 24576
    worker.optimizer.zero_grad(set_to_none=True)
    torch.cuda.reset_peak_memory_stats()
    token_id = worker.tokenizer.encode('x', add_special_tokens=False)[0]
    ids = torch.full((1, size), token_id, dtype=torch.long, device='cuda')
    position_ids = torch.arange(size, device='cuda').unsqueeze(0)
    with torch.autocast(device_type='cuda', dtype=worker.dtype):
        output = worker.model(input_ids=ids, attention_mask=torch.ones_like(ids),
                              position_ids=position_ids, use_cache=False)
    logits = worker._apply_temperature_scaling(output.logits)
    del output
    # Targets are synthetic supported actions solely to allocate the same masked
    # differentiable filter. They are never recorded as generated responses.
    target = logits[:, :-1].detach().argmax(-1)
    mask = torch.zeros_like(target)
    mask[:, -16384:] = 1
    q = selected_logprobs(logits[:, :-1], target, mask)
    (-q.sum() / mask.sum()).backward()
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in worker.model.parameters())
    peak = torch.cuda.max_memory_allocated()
    worker.optimizer.zero_grad(set_to_none=True)
    del logits, q, ids, target, mask
    torch.cuda.empty_cache()
    json_receipt('full_context.json', {'status': 'PASS', 'sequence_length': size,
                 'synthetic_assistant_loss_tokens': 16384, 'peak_allocated_bytes': peak,
                 'optimizer_state_resident': True, 'optimizer_updates_in_memory_control': 0,
                 'scientific_responses_in_memory_control': 0})
