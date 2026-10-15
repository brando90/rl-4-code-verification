"""Enforce technical attempt finality, published recovery evidence and preflight chronology."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_technical_ledger', PHASE/'technical_ledger.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def file_ref(path, value):
    path.write_text(json.dumps(value, sort_keys=True))
    return {'path': str(path), 'sha256': m.digest(path), 'revision': 'authored-fixture'}


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(m, 'verify_publication', lambda path, repo, rev: json.loads(Path(path).read_text()))
    science = {k: 'fixed-'+k for k in m.SCIENCE_KEYS}
    implementation = tmp_path/'launcher.txt'; implementation.write_text('original')
    lock = {'gate': 'LP', 'condition': 'v2-S2', 'status': 'FROZEN', 'science': science,
            'configuration': {'technical_ledger': str(tmp_path/'ledger')},
            'bindings': [{'path': str(PHASE/'technical_ledger.py'), 'sha256': m.digest(PHASE/'technical_ledger.py')},
                         {'path': str(implementation), 'sha256': m.digest(implementation)}]}
    lp = file_ref(tmp_path/'LP.json', lock)
    health = {'status': 'PASS', 'scope': 'non-probe infrastructure only', 'admission_statistics_computed': False,
              'generated_tokens': 1, 'visible_index': '2'}
    preflight = file_ref(tmp_path/'preflight.json', health)
    kwargs = {'LP': lp, 'repository': tmp_path, 'preflight': preflight, 'prerequisites': {}}
    return kwargs, lock, implementation


def admitted(tmp_path, monkeypatch):
    kwargs, lock, implementation = fixture(tmp_path, monkeypatch)
    root, record = m.admit(tmp_path/'ledger', 'T1', **kwargs)
    return root, record, kwargs, lock, implementation


def evidence(tmp_path):
    path = tmp_path/'private_error.log'; path.write_text('authored reproducible defect')
    return {'reproducible_defect': 'authored launcher exception', 'bindings': [{'path': str(path), 'sha256': m.digest(path)}]}


def test_failed_preflight_never_counts_and_final_fail_never_retries(tmp_path, monkeypatch):
    kwargs, _, _ = fixture(tmp_path, monkeypatch)
    bad = json.loads(Path(kwargs['preflight']['path']).read_text()); bad['visible_index'] = 'GPU-uuid'
    original = kwargs['preflight']; kwargs['preflight'] = file_ref(tmp_path/'bad.json', bad)
    with pytest.raises(ValueError, match='preflight'): m.admit(tmp_path/'ledger', 'T1', **kwargs)
    assert not (tmp_path/'ledger').exists()
    kwargs['preflight'] = original
    root, record = m.admit(tmp_path/'ledger', 'T1', **kwargs)
    raw = tmp_path/'raw.json'; raw.write_text('[]')
    bindings = [{'path': str(raw), 'sha256': m.digest(raw)}]
    result = m.evaluate_once(root, bindings, lambda: {'condition': 'v2-S2', 'gate': 'T1', 'status': 'FAIL', 'admission_statistics_computed': True})
    assert result['attempt'] == 1
    with pytest.raises(RuntimeError, match='final'): m.admit(tmp_path/'ledger', 'T1', **kwargs)
    with pytest.raises(RuntimeError, match='closed'): m.evaluate_once(root, bindings, lambda: pytest.fail('second statistic'))


def test_interrupted_statistic_evaluation_is_still_final(tmp_path, monkeypatch):
    root, _, kwargs, _, _ = admitted(tmp_path, monkeypatch)
    raw = tmp_path/'raw'; raw.write_text('raw')
    def broken(): raise RuntimeError('after evaluation began')
    with pytest.raises(RuntimeError, match='evaluation began'):
        m.evaluate_once(root, [{'path': str(raw), 'sha256': m.digest(raw)}], broken)
    with pytest.raises(RuntimeError, match='final'): m.admit(tmp_path/'ledger', 'T1', **kwargs)
    with pytest.raises(RuntimeError, match='final'):
        m.finish_infrastructure(root, evidence=evidence(tmp_path), cleanup_verified=True)


def test_recovery_requires_unchanged_science_and_published_regression(tmp_path, monkeypatch):
    root, record, kwargs, old, implementation = admitted(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError, match='unresolved'): m.admit(tmp_path/'ledger', 'T1', **kwargs)
    result = m.finish_infrastructure(root, evidence=evidence(tmp_path), cleanup_verified=True)
    with pytest.raises(RuntimeError, match='published A4 fix'): m.admit(tmp_path/'ledger', 'T1', **kwargs)
    implementation.write_text('fixed launcher')
    new = json.loads(json.dumps(old)); new['bindings'][1]['sha256'] = m.digest(implementation)
    current = file_ref(tmp_path/'LP2.json', new)
    regression = file_ref(tmp_path/'regression.json', {'status': 'PASS', 'exit_code': 0, 'reproduced_original_defect': True})
    prior_result = file_ref(tmp_path/'published_failure.json', result)
    successor = file_ref(tmp_path/'fix.json', {'gate': 'A4_TECHNICAL_FIX', 'status': 'FROZEN',
        'previous_LP_sha256': kwargs['LP']['sha256'], 'successor_LP_sha256': current['sha256'],
        'science_sha256': record['science_sha256'], 'regression_test': regression, 'failed_attempt_result': prior_result,
        'changed_bindings': [{'path': str(implementation), 'previous_sha256': old['bindings'][1]['sha256'],
                              'successor_sha256': m.digest(implementation), 'reason': 'authored numeric index fix'}]})
    kwargs['LP'] = current
    second, record2 = m.admit(tmp_path/'ledger', 'T1', successor=successor, **kwargs)
    assert second.name == 'attempt_2' and record2['science_sha256'] == record['science_sha256']
    changed = json.loads(json.dumps(new)); changed['science']['sampler'] = 'changed'
    kwargs['LP'] = file_ref(tmp_path/'changed.json', changed)
    with pytest.raises(ValueError, match='science changed'): m.admit(tmp_path/'ledger', 'T1', **kwargs)


def test_changed_raw_input_refused_before_statistic_and_cleanup_required(tmp_path, monkeypatch):
    root, _, _, _, _ = admitted(tmp_path, monkeypatch)
    raw = tmp_path/'raw'; raw.write_text('before'); binding = {'path': str(raw), 'sha256': m.digest(raw)}
    raw.write_text('after')
    with pytest.raises(ValueError, match='input changed'): m.evaluate_once(root, [binding], lambda: pytest.fail('evaluated changed input'))
    assert not (root/'evaluation_attempt.json').exists()
    with pytest.raises(ValueError, match='cleanup'):
        m.finish_infrastructure(root, evidence=evidence(tmp_path), cleanup_verified=False)
    assert not (root/'result.json').exists()


def test_preceding_same_science_gate_pass_is_required(tmp_path, monkeypatch):
    kwargs, lock, _ = fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='prerequisite'): m.admit(tmp_path/'ledger', 'T2', **kwargs)
    result = {'condition': 'v2-S2', 'gate': 'T1', 'status': 'PASS', 'admission_statistics_computed': True,
              'science_sha256': m.signature(lock['science'])}
    kwargs['prerequisites'] = {'T1': file_ref(tmp_path/'T1.json', result)}
    root, record = m.admit(tmp_path/'ledger', 'T2', **kwargs)
    assert record['gate'] == 'T2'
    result['science_sha256'] = 'changed'
    kwargs['prerequisites'] = {'T1': file_ref(tmp_path/'T1_changed.json', result)}
    with pytest.raises(ValueError, match='same-science PASS'): m.admit(tmp_path/'different', 'T2', **kwargs)
    with pytest.raises(ValueError, match='only covers'): m.admit(tmp_path/'different', 'T5', **kwargs)


def test_three_attempt_bound_and_ledger_root_cannot_reset(tmp_path, monkeypatch):
    kwargs, lock, _ = fixture(tmp_path, monkeypatch)
    for number in (1, 2, 3):
        path = tmp_path/'ledger/T1'/f'attempt_{number}'
        path.mkdir(parents=True)
        (path/'attempt.json').write_text('{}')
    with pytest.raises(RuntimeError, match='three technical attempts exhausted'):
        m.admit(tmp_path/'ledger', 'T1', **kwargs)
    with pytest.raises(ValueError, match='cannot move or reset'):
        m.admit(tmp_path/'new_ledger', 'T1', **kwargs)
