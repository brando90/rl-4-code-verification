"""Exercise train-only manifests, irreversible slot ledgers and independent batch ordering."""
import importlib.util
from pathlib import Path
import hashlib
import json

import pytest

P = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/panel.py'
SPEC = importlib.util.spec_from_file_location('e13_phase1_panel', P)
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)


def fixture(batch='lp1'):
    train = [f't{i}' for i in range(539)]
    tasks = sorted(train, key=lambda t: hashlib.sha256(('e13v2-lp1\0'+t).encode()).hexdigest())[:8] if batch == 'lp1' else train
    cells = [{'cell_id': f'{batch}/{t}/{s}', 'task_id': t, 'sample': s, 'split': 'train',
              'prompt_token_ids': [1, 2], 'seed': M.cell_seed(batch, t, s)}
             for t in tasks for s in (range(1) if batch == 'lp1' else range(8))]
    return {'batch': batch, 'cells': cells, 'max_model_len': 16384, 'terminal_token_ids': [9]}, train


def generated(cell):
    return {'prompt_token_ids': cell['prompt_token_ids'], 'output_token_ids': [3, 9],
            'generation_logprobs': [-1., -1.], 'finish_reason': 'stop'}


def test_denominator_and_independent_seeds():
    seeds = []
    for batch in M.BATCHES:
        manifest, train = fixture(batch)
        M.validate_manifest(manifest, train)
        seeds.extend(c['seed'] for c in manifest['cells'])
    assert len(set(seeds)) == len(seeds)
    manifest['cells'].pop()
    with pytest.raises(ValueError, match='incomplete'):
        M.validate_manifest(manifest, train)


@pytest.mark.parametrize('change', ['test', 'seed', 'prompt', 'cap', 'selection'])
def test_bad_manifest_rejected_before_call(change, tmp_path):
    manifest, train = fixture(); calls = []
    if change == 'test': manifest['cells'][0]['split'] = 'test'
    if change == 'seed': manifest['cells'][0]['seed'] += 1
    if change == 'prompt': manifest['cells'][0]['prompt_token_ids'] = []
    if change == 'cap': manifest['max_model_len'] = 8192
    if change == 'selection': manifest['cells'][0]['sample'] = 1
    with pytest.raises(ValueError):
        M.generate_once(manifest, train, tmp_path, lambda c: calls.append(c), lease_check=lambda: None, prerequisites={})
    assert not calls and not (tmp_path/'attempt.json').exists()


def test_no_retry_after_partial_failure(tmp_path):
    manifest, train = fixture(); calls = []
    def engine(cell):
        calls.append(cell)
        if len(calls) == 2: raise RuntimeError('transport failure')
        return generated(cell)
    with pytest.raises(RuntimeError):
        M.generate_once(manifest, train, tmp_path, engine, lease_check=lambda: None, prerequisites={})
    terminal = json.loads((tmp_path/'terminal.json').read_text())
    assert terminal['completed'] == 1 and terminal['declared'] == 8
    with pytest.raises(FileExistsError):
        M.generate_once(manifest, train, tmp_path, engine, lease_check=lambda: None, prerequisites={})
    assert len(calls) == 2


def test_cap_is_metadata_and_does_not_set_strict_zero(tmp_path):
    manifest, train = fixture()
    def engine(cell):
        return {**generated(cell), 'output_token_ids': [3]*8192,
                'generation_logprobs': [-1.]*8192, 'finish_reason': 'length'}
    M.generate_once(manifest, train, tmp_path, engine, lease_check=lambda: None, prerequisites={})
    row = json.loads((tmp_path/'00000.generation.json').read_text())
    assert row['at_token_cap'] and 'strict' not in row


def test_independent_batch_requires_freeze():
    with pytest.raises(ValueError, match='LP-1'):
        M.check_prerequisites('base')
    with pytest.raises(ValueError, match='freeze'):
        M.check_prerequisites('full2', lp1={'status': 'PASS'})
    M.check_prerequisites('full2', lp1={'status': 'PASS'}, calibration={'status': 'FROZEN', 'F2': .75})
