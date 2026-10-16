"""Reject incomplete final evidence and preserve other content on repeat publication."""
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('e08_finalize', HERE / 'finalize_results.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def test_incomplete_evidence_cannot_finalize(tmp_path, monkeypatch):
    monkeypatch.setattr(m, 'HERE', tmp_path)
    (tmp_path / 'results').mkdir()
    (tmp_path / 'results/ladder_manifest_v3.json').write_text('{}')
    (tmp_path / 'results/validation_summary_v3.json').write_text(json.dumps({'known_cells': 1080, 'declared_cells': 17280}))
    with pytest.raises(AssertionError, match='incomplete'):
        m.validate()
    assert not (tmp_path / 'results/completion_validation_v3.json').exists()


def test_owned_block_replacement_preserves_later_other_results():
    text = m.replace_block('prior report\n', 'OWNED', 'first result') + '\nother owner result\n'
    replaced = m.replace_block(text, 'OWNED', 'updated result')
    assert replaced.startswith('prior report\n') and replaced.endswith('\nother owner result\n')
    assert 'first result' not in replaced and replaced.count('updated result') == 1


def test_missing_namespace_receipts_cannot_claim_completion():
    with pytest.raises(AssertionError, match='diagnostic remains incomplete'):
        m.validate_namespace({'declared_cells': 1080, 'unknown_cells': 1}, [], {})


def namespace_fixture(tmp_path, timeout):
    path = tmp_path / 'solution.lean'; path.write_text('example : True := by trivial\n')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = [{'task_id': f't{i}', 'sample_idx': '0', 'changed': 'False', 'original_kernel_binary': '0',
             'diagnostic_kernel_binary': '0', 'original_sha256': digest, 'transformed_sha256': digest}
            for i in range(1080)]
    rows[0].update(changed='True', diagnostic_kernel_binary='' if timeout else '1')
    primary = {(r['task_id'], '0'): {'kernel_binary': '0'} for r in rows}
    receipt = {'task_id': 't0', 'sample_idx': 0, 'kernel_binary': None if timeout else 1,
               'compile_timeout': timeout, 'compiles': not timeout, 'path': str(path),
               'original_sha256': digest, 'transformed_sha256': digest}
    path.with_suffix('.json').write_text(json.dumps(receipt))
    diag = {'declared_cells': 1080, 'unknown_cells': int(timeout), 'changed_cells': 1,
            'changed_receipts': [receipt], 'original_successes': 0, 'diagnostic_successes_known': 0 if timeout else 1}
    if not timeout:
        diag['paired_task_bootstrap_delta'] = {'draws': 10000, 'seed': 0, 'unit': 'task with eight attempts together',
                                              'mean': 1 / 1080, 'ci95': [0, .01]}
    return diag, rows, primary


@pytest.mark.parametrize('timeout', [False, True])
def test_complete_diagnostic_coverage_retains_native_timeout(tmp_path, timeout):
    diag, rows, primary = namespace_fixture(tmp_path, timeout)
    m.validate_namespace(diag, rows, primary)
    assert diag['unknown_cells'] == int(timeout)


@pytest.mark.parametrize('corruption', ['unknown_count', 'timeout_to_zero', 'unknown_without_timeout',
                                       'unexecuted_unchanged', 'point_estimate', 'missing_receipt', 'modified_source'])
def test_incomplete_or_fabricated_diagnostic_evidence_rejected(tmp_path, corruption):
    diag, rows, primary = namespace_fixture(tmp_path, True)
    if corruption == 'unknown_count': diag['unknown_cells'] = 0
    elif corruption == 'timeout_to_zero': diag['changed_receipts'][0]['kernel_binary'] = 0
    elif corruption == 'unknown_without_timeout': diag['changed_receipts'][0]['compile_timeout'] = False
    elif corruption == 'unexecuted_unchanged':
        rows[1]['diagnostic_kernel_binary'] = ''; diag['unknown_cells'] = 2
    elif corruption == 'point_estimate': diag['paired_task_bootstrap_delta'] = {}
    elif corruption == 'missing_receipt': diag['changed_receipts'] = []
    else: Path(diag['changed_receipts'][0]['path']).write_text('changed')
    with pytest.raises((AssertionError, ValueError)):
        m.validate_namespace(diag, rows, primary)


def test_reduced_bootstrap_cannot_claim_frozen_analysis():
    with pytest.raises(AssertionError):
        m.validate_bootstrap({'draws': 999, 'seed': 0})
