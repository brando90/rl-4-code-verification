"""Reject incomplete or scientifically changed remote generation handoffs."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('e08_remote_generation', HERE / 'remote_generation.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture_rows():
    ids = [f'task_{n}' for n in range(135)]
    prompts = {t: {'prompt_sha256': t + '_hash'} for t in ids}
    rows = [{'task_id': t, 'sample_idx': s, 'label': 'v3_E_1p7b_f0p5_g8', 'backend': 'vllm',
             'prompt_sha256': t + '_hash', 'generated_tokens': 120,
             'sampling': {'temperature': .6, 'top_p': .95, 'top_k': 20, 'max_tokens': 12288,
                          'seed': 91 * 100003 + s, 'thinking': 'on', 'stop_tokens': ['<|im_end|>']}}
            for t in ids for s in range(8)]
    return ids, prompts, rows


def test_exact_handoff_and_duplicated_missing_cell(tmp_path):
    ids, prompts, rows = fixture_rows(); path = tmp_path / 'raw.jsonl'
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    assert m.validate_raw(path, 'v3_E_1p7b_f0p5', ids, prompts)['cells'] == 1080
    rows[-1] = copy.deepcopy(rows[0])
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    with pytest.raises(AssertionError, match='Missing, extra or duplicate'):
        m.validate_raw(path, 'v3_E_1p7b_f0p5', ids, prompts)


@pytest.mark.parametrize('mutation', ['seed', 'prompt', 'token_cap'])
def test_changed_scientific_input_rejected(tmp_path, mutation):
    ids, prompts, rows = fixture_rows(); path = tmp_path / 'raw.jsonl'
    if mutation == 'seed': rows[0]['sampling']['seed'] += 1
    if mutation == 'prompt': rows[0]['prompt_sha256'] = 'wrong'
    if mutation == 'token_cap': rows[0]['generated_tokens'] = 12289
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    with pytest.raises(AssertionError):
        m.validate_raw(path, 'v3_E_1p7b_f0p5', ids, prompts)
