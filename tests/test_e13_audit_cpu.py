"""Check audit score reuse, hidden missingness and exclusive processor measurement receipts."""
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

PHASE = Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_audit_cpu', PHASE/'audit_cpu.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture(tmp_path, variant='original'):
    train = tmp_path/'train.txt'; train.write_text('authored\n')
    source = tmp_path/'source.lean'; source.write_text('theorem value : 1 = 1 := rfl\n')
    suite = tmp_path/'suite.json'; suite.write_text('{}')
    score = tmp_path/'original.json'; score.write_text(json.dumps({'status': 'measured', 'strict': 1,
        'compile': True, 'task_id': 'authored', 'sample_idx': 0, 'batch': 'full1', 'source_sha256': m.digest(source)}))
    ref = lambda p: {'path': str(p), 'sha256': m.digest(p)}
    cell = {'cell_id': 'authored/'+variant, 'audit_id': 'authored', 'task_id': 'authored',
            'split': 'train', 'variant': variant, 'group_id': 'group', 'source': ref(source), 'original_score': ref(score)}
    root = tmp_path/'cell'; root.mkdir()
    config = {'root': str(tmp_path/'execution'), 'train_ids': str(train), 'lake': 'unused', 'scorer': 'unused'}
    identity = {k: cell[k] for k in ('cell_id', 'audit_id', 'task_id', 'group_id', 'split', 'variant')}
    job = {'cell': cell, 'configuration': config, 'identity': identity, 'root': str(root),
           'suite': ref(suite), 'execution_sha256': 'authored-lock'}
    return job


def test_original_strict_is_reused_and_partial_hidden_rate_remains_missing(tmp_path):
    job = fixture(tmp_path)
    result = m.measure(job, inspector=lambda *_a, **_k: pytest.fail('original rescored'),
        hidden=lambda *_: {'status': 'incomplete', 'fully_applicable': False, 'hidden_pass_rate': 1., 'n_evaluable': 1, 'n_tests': 2})
    assert result['strict'] == 1 and result['compile'] is True
    assert result['hidden_test_coverage'] is None and not result['new_strict_measurement']
    assert json.loads(Path(result['hidden_receipt']['path']).read_text())['hidden_pass_rate'] == 1.
    with pytest.raises(RuntimeError, match='never rerun'): m.measure(job)


def test_mutation_scores_once_then_independent_hidden_failure_is_zero(tmp_path):
    job = fixture(tmp_path, 'deletion'); calls = []
    def inspect(source, **kwargs):
        calls.append(source)
        root = kwargs['evidence']/'oracle'; root.mkdir(parents=True)
        (root/'oracle.json').write_text(json.dumps({'compile': False}))
        return {'strict': 0, 'source_sha256': m.digest(source), 'factored_reward': .3}
    result = m.measure(job, inspector=inspect,
        hidden=lambda *_: {'status': 'compile_failure', 'fully_applicable': False, 'hidden_pass_rate': 0.})
    assert len(calls) == 1 and result['new_strict_measurement']
    assert result['strict'] == 0 and result['compile'] is False and result['hidden_test_coverage'] == 0


def test_missing_source_has_no_measurement_and_heldout_is_refused(tmp_path):
    job = fixture(tmp_path); job['cell'].update(source=None, reason='source unavailable')
    result = m.measure(job, inspector=lambda *_a, **_k: pytest.fail('missing measured'))
    assert result['status'] == 'MISSING_INPUT' and result['strict'] is None
    job['cell']['split'] = 'test'
    with pytest.raises(ValueError, match='train-only'): m.measure(job)


def test_completed_cell_recovery_and_changed_execution_refusal(tmp_path):
    job = fixture(tmp_path); calls = []
    def execute(job, root, marker, slots):
        calls.append(marker)
        result = {**job['identity'], 'status': 'ACCOUNTED', 'strict': 1, 'cleanup_verified': True}
        m.write_new(root/'result.json', result)
        return result
    args = (job['cell'], 0, job['configuration'], job['suite'])
    first = m.score_cell(*args, 'fixed', None, executor=execute)
    assert m.score_cell(*args, 'fixed', None, executor=execute) == first and len(calls) == 1
    with pytest.raises(ValueError, match='binding changed'): m.score_cell(*args, 'changed', None, executor=execute)


def test_interrupted_cell_recovers_evidence_without_second_execution(tmp_path, monkeypatch):
    job = fixture(tmp_path)
    def interrupted(*_): raise OSError('authored interruption')
    args = (job['cell'], 0, job['configuration'], job['suite'], 'fixed', None)
    with pytest.raises(OSError): m.score_cell(*args, executor=interrupted)
    calls = []
    def finish(root, expected, marker):
        calls.append(marker)
        return {**expected, 'status': 'unresolved_measurement', 'cleanup_verified': True}
    monkeypatch.setattr(m, 'finish_attempt', finish)
    assert m.score_cell(*args, executor=lambda *_: pytest.fail('interruption rerun'))['status'] == 'unresolved_measurement'
    assert len(calls) == 1


def test_authored_real_oracle_and_hidden_suite_end_to_end(tmp_path):
    keys = ('E13_LAKE_DIR', 'E13_SCORER_ROOT')
    if not all(os.environ.get(k) and Path(os.environ[k]).exists() for k in keys):
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION') == '1': pytest.fail('required Lean route unavailable')
        pytest.skip('Lean route unavailable')
    from extract_hidden_tests import extract
    job = fixture(tmp_path, 'padding')
    source = ('import Mathlib\ndef increment (n : Nat) : Nat := n + 1\n'
              'example : increment 2 = 3 := rfl\n'
              'theorem correct (n : Nat) : increment n = n + 1 := rfl\n')
    path = Path(job['cell']['source']['path']); path.write_text(source)
    job['cell']['source']['sha256'] = m.digest(path)
    suite = Path(job['suite']['path']); suite.write_text(json.dumps(extract(source)))
    job['suite']['sha256'] = m.digest(suite)
    job['configuration'].update(lake=os.environ['E13_LAKE_DIR'], scorer=os.environ['E13_SCORER_ROOT'],
                                lake_bin=str(Path.home()/'.elan/bin/lake'))
    result = m.measure(job)
    assert result['strict'] == 1 and result['compile'] is True
    assert result['hidden_status'] == 'measured' and result['hidden_test_coverage'] == 1.
    assert result['components']['p'] == {'numerator': 1, 'denominator': 1}
