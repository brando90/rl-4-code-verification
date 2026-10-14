"""Detect token shifts, dropped EOS, support errors and probability mismatches."""
import copy
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/probability.py'
SPEC = importlib.util.spec_from_file_location('e13_phase1_probability', PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def receipt():
    return {'cell_id': 'probe/train/0', 'split': 'train',
            'prompt_token_ids': [3, 4], 'output_token_ids': [5, 6, 2],
            'trainer_input_ids': [3, 4, 5, 6, 2],
            'trainer_token_mask': [0, 0, 1, 1, 1], 'finish_reason': 'stop',
            'generation_logprobs': [-1., -2., -3.],
            'trainer_logprobs': [float('nan'), float('nan'), -1., -2., -3.]}


def run(row):
    return MODULE.assess_probability([row], eos_token_ids=[2])


def test_probability_includes_eos_and_excludes_prompt():
    out = run(receipt())
    assert out['status'] == 'PASS'
    assert out['generated_tokens'] == 3 and out['prompt_tokens'] == 2
    assert out['eos_tokens_in_mask'] == 1


@pytest.mark.parametrize('key,value', [
    ('trainer_token_mask', [0, 0, 1, 1, 0]),
    ('trainer_input_ids', [3, 4, 6, 5, 2]),
    ('generation_logprobs', [-1., -2.]),
    ('split', 'validation'),
    ('finish_reason', 'length'),
    ('output_token_ids', []),
])
def test_malformed_receipt_is_not_silently_dropped(key, value):
    row = receipt(); row[key] = value
    with pytest.raises(ValueError):
        run(row)


@pytest.mark.parametrize('value', [float('-inf'), float('inf'), float('nan')])
def test_unsupported_token_fails_even_with_other_exact_probabilities(value):
    row = receipt(); row['generation_logprobs'][1] = value
    out = run(row)
    assert out['status'] == 'FAIL' and out['unsupported_tokens'] == 1
    assert out['generated_tokens'] == 3


def test_likelihood_ratio_direction_and_eos_error_are_checked():
    row = receipt(); row['trainer_logprobs'][-1] = -2.
    out = run(row)
    assert out['status'] == 'FAIL'
    assert out['importance_truncated_tokens'] == 1
    assert out['importance_truncation_fraction'] == 1/3
    row['trainer_logprobs'][-1] = -4.
    out = run(row)
    assert out['status'] == 'FAIL' and out['importance_truncated_tokens'] == 0


def test_duplicate_cell_cannot_inflate_probe_denominator():
    with pytest.raises(ValueError):
        MODULE.assess_probability([receipt(), copy.deepcopy(receipt())], eos_token_ids=[2])
