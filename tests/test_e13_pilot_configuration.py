"""Keep S2 generation fixed while deriving training memory settings and final arm transitions."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_pilot_configuration', PHASE/'pilot_configuration.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def policy():
    return {'precision': 'float16', 'model_name': '/authored-model', 'tokenizer': {'name': '/authored-tokenizer'},
        'generation': {'temperature': 1., 'top_p': 1., 'top_k': -1, 'max_new_tokens': 8192,
            'stop_token_ids': [151643, 151645], 'eos_token_id': 151643, 'pad_token_id': 151643,
            'vllm_cfg': {'precision': 'float16', 'enforce_eager': True, 'max_model_len': 15945, 'tensor_parallel_size': 1}},
        'generation_batch_size': 32, 'logprob_batch_size': 1, 'max_total_sequence_length': 15945,
        'dtensor_cfg': {'enabled': True, '_v2': False, 'tensor_parallel_size': 1, 'context_parallel_size': 1,
                        'activation_checkpointing': False, 'cpu_offload': False},
        'megatron_cfg': {'enabled': False}, 'dynamic_batching': {'enabled': False}, 'sequence_packing': {'enabled': False},
        'optimizer': {'name': 'torch.optim.AdamW', 'kwargs': {'lr': 1e-6, 'betas': [.9, .999], 'eps': 1e-8,
            'weight_decay': .01, 'foreach': False, 'fused': False}}, 'train_micro_batch_size': 1,
        'max_grad_norm': 1., 'train_global_batch_size': 512, 'scheduler': [{'name': 'authored-inference-schedule'}]}


def test_exactly_four_prospective_changes_preserve_generator_and_source(tmp_path):
    original = policy(); saved = copy.deepcopy(original)
    after, delta = m.derive(original)
    assert original == saved and set(delta) == m.CHANGED
    assert after['generation'] == original['generation'] and after['tokenizer'] == original['tokenizer']
    assert after['scheduler'] == m.SCHEDULER and after['train_global_batch_size'] == 256
    path = tmp_path/'original.json'; path.write_text(json.dumps(original))
    receipt = m.prepare_policy(path, m.digest(path), tmp_path/'prepared.json')
    assert receipt['status'] == 'PREPARED_NOT_ADMITTED'
    assert receipt['loss']['truncated_importance_sampling_ratio'] == 2.
    with pytest.raises(FileExistsError): m.prepare_policy(path, m.digest(path), tmp_path/'prepared.json')
    with pytest.raises(ValueError, match='frozen hash'): m.prepare_policy(path, '0'*64, tmp_path/'other.json')


@pytest.mark.parametrize('mutate', [
    lambda p: p['generation'].update(top_p=.9),
    lambda p: p.update(precision='bfloat16'),
    lambda p: p.update(generation_batch_size=16),
    lambda p: p['optimizer']['kwargs'].update(lr=5e-6),
    lambda p: p['dtensor_cfg'].update(tensor_parallel_size=2),
])
def test_sampler_precision_batch_optimizer_and_parallel_changes_refused(mutate):
    value = policy(); mutate(value)
    with pytest.raises(ValueError): m.derive(value)


def gates():
    return [{'gate': 'G0_A3', 'status': 'PASS'},
            {'condition': 'v2-S2', 'status': 'PASS', 'numerical_dtype': 'float16', 'admission_statistics_computed': True},
            {'condition': 'v2-S2', 'status': 'FROZEN', 'C_calibration_admitted': True},
            {'gate': 'G1', 'status': 'PASS'}, {'gate': 'H2', 'status': 'PASS'}]


def test_final_C_failure_keeps_A_B_P_but_unfinished_gates_are_not_failures():
    inputs = gates(); assert m.select_arms(*inputs)['eligible_arms'] == ['A', 'B', 'C', 'P']
    inputs[3]['status'] = 'FAIL'
    assert m.select_arms(*inputs)['eligible_arms'] == ['A', 'B', 'P']
    inputs[3]['status'] = 'INCONCLUSIVE'
    assert m.select_arms(*inputs)['eligible_arms'] == ['A', 'B', 'P']
    inputs[3]['status'] = 'INCOMPLETE'
    with pytest.raises(ValueError, match='unfinished'): m.select_arms(*inputs)
    inputs = gates(); inputs[0]['status'] = 'FAIL'
    with pytest.raises(ValueError, match='G0'): m.select_arms(*inputs)
    inputs = gates(); inputs[2]['C_calibration_admitted'] = False
    assert m.select_arms(*inputs)['eligible_arms'] == ['A', 'B', 'P']
