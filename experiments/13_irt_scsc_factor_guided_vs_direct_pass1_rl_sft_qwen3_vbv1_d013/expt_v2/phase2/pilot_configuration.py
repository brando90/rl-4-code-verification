"""Derive the prospective one-device training configuration without changing admitted S2 generation."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from training_checkpoint import digest, write_new

LOSS = {'reference_policy_kl_penalty': 0., 'ratio_clip_min': .2, 'ratio_clip_max': .28,
        'ratio_clip_c': None, 'use_on_policy_kl_approximation': False,
        'use_importance_sampling_correction': True, 'truncated_importance_sampling_ratio': 2.,
        'token_level_loss': True, 'sequence_level_importance_ratios': False}
SCHEDULER = {'name': 'torch.optim.lr_scheduler.ConstantLR', 'kwargs': {'factor': 1., 'total_iters': 10**10}}
CHANGED = {'dtensor_cfg.activation_checkpointing', 'dtensor_cfg.cpu_offload',
           'train_global_batch_size', 'scheduler'}


def changes(before, after, prefix=''):
    if isinstance(before, dict) and isinstance(after, dict):
        result = {}
        for key in before.keys() | after.keys():
            path = prefix+'.'+key if prefix else key
            if key not in before or key not in after:
                result[path] = {'before': before.get(key), 'after': after.get(key)}
            else:
                result.update(changes(before[key], after[key], path))
        return result
    return {} if before == after else {prefix: {'before': before, 'after': after}}


def validate_inference(policy):
    generation = policy['generation']; engine = generation['vllm_cfg']
    expected = {'temperature': 1., 'top_p': 1., 'top_k': -1, 'max_new_tokens': 8192,
                'stop_token_ids': [151643, 151645], 'eos_token_id': 151643, 'pad_token_id': 151643}
    if any(generation.get(k) != v for k, v in expected.items()):
        raise ValueError('admitted generator sampler or token contract changed')
    if (policy['precision'] != 'float16' or engine['precision'] != 'float16'
            or engine['enforce_eager'] is not True or engine['max_model_len'] != 15945
            or engine['tensor_parallel_size'] != 1 or policy['generation_batch_size'] != 32
            or policy['logprob_batch_size'] != 1 or policy['max_total_sequence_length'] != 15945):
        raise ValueError('admitted S2 engine or probability batch changed')
    if (not policy['dtensor_cfg']['enabled'] or policy['dtensor_cfg']['_v2'] is not False
            or policy['dtensor_cfg']['tensor_parallel_size'] != 1
            or policy['dtensor_cfg']['context_parallel_size'] != 1
            or policy['megatron_cfg']['enabled'] is not False
            or policy['dynamic_batching']['enabled'] is not False
            or policy['sequence_packing']['enabled'] is not False):
        raise ValueError('installed single-device DTensor implementation changed')
    if policy['optimizer'] != {'name': 'torch.optim.AdamW', 'kwargs': {
            'lr': 1e-6, 'betas': [.9, .999], 'eps': 1e-8, 'weight_decay': .01, 'foreach': False, 'fused': False}}:
        raise ValueError('prospective optimizer differs from the existing scientific configuration')
    if policy['train_micro_batch_size'] != 1 or policy['max_grad_norm'] != 1.:
        raise ValueError('microbatch or gradient clipping changed')


def derive(original):
    validate_inference(original)
    if (original['dtensor_cfg']['activation_checkpointing'] is not False
            or original['dtensor_cfg']['cpu_offload'] is not False
            or original['train_global_batch_size'] != 512 or not isinstance(original['scheduler'], list)):
        raise ValueError('expected immutable LP-1 inference policy before prospective training changes')
    result = copy.deepcopy(original)
    result['dtensor_cfg']['activation_checkpointing'] = True
    result['dtensor_cfg']['cpu_offload'] = True
    result['train_global_batch_size'] = 256
    result['scheduler'] = copy.deepcopy(SCHEDULER)
    validate_inference(result)
    delta = changes(original, result)
    if set(delta) != CHANGED:
        raise ValueError('unregistered policy change')
    return result, delta


def prepare_policy(source, expected_sha256, destination):
    """Prepare bytes for a future LP lock; this does not admit a device call."""
    if digest(source) != expected_sha256:
        raise ValueError('S2 policy source differs from its frozen hash')
    original = json.loads(Path(source).read_text())
    policy, delta = derive(original)
    destination = Path(destination)
    write_new(destination, policy)
    return {'condition': 'v2-S2', 'status': 'PREPARED_NOT_ADMITTED',
            'source': str(source), 'source_sha256': expected_sha256,
            'policy': str(destination), 'policy_sha256': digest(destination), 'changes': delta,
            'loss': copy.deepcopy(LOSS), 'minimum_device_memory_mib': 75000,
            'minimum_host_available_bytes': 256*1024**3,
            'learning_rate_function': 'constant 1e-6 for every consumed-token fraction, identical across arms',
            'resource_caps': 'must be frozen separately before any claim or stage'}


def select_arms(g0, lp1, calibration, g1, h2):
    """Apply PLAN's final scientific transitions; unfinished gates never silently disable C."""
    if g0.get('gate') != 'G0_A3' or g0.get('status') != 'PASS':
        raise ValueError('G0 did not admit Phase 2')
    if (lp1.get('condition') != 'v2-S2' or lp1.get('status') != 'PASS'
            or lp1.get('numerical_dtype') != 'float16' or lp1.get('admission_statistics_computed') is not True):
        raise ValueError('final S2 LP-1 PASS required')
    if (calibration.get('status') != 'FROZEN' or calibration.get('condition') != 'v2-S2'
            or type(calibration.get('C_calibration_admitted')) is not bool):
        raise ValueError('calibration transition remains unresolved')
    for value, name in ((g1, 'G1'), (h2, 'H2')):
        if value.get('gate') != name or value.get('status') not in ('PASS', 'FAIL', 'INCONCLUSIVE'):
            raise ValueError('scientific gate is unfinished')
    disabled = []
    if not calibration['C_calibration_admitted']: disabled.append('calibration or variance admission')
    if g1['status'] != 'PASS': disabled.append('G1 '+g1['status'])
    if h2['status'] != 'PASS': disabled.append('H2 '+h2['status'])
    return {'eligible_arms': ['A', 'B', 'P'] if disabled else ['A', 'B', 'C', 'P'],
            'disabled_C_reasons': disabled, 'source': 'PLAN section 4 transition table',
            'technical_and_learning_gates_still_required': True}
