"""Exercise corrected hidden-test mapping, real Lean checks and durable train-only execution."""
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_hidden_runtime', PHASE/'hidden_runtime.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from extract_hidden_tests import extract

GOLD = 'import Mathlib\ndef increment (n : Nat) : Nat := n + 1\nexample : increment 2 = 3 := rfl\n'


def runtime(tmp_path):
    lake = os.environ.get('E13_LAKE_DIR')
    lake_bin = Path.home()/'.elan/bin/lake'
    if not lake or not Path(lake).exists() or not lake_bin.exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION') == '1':
            pytest.fail('required Lean route unavailable')
        pytest.skip('Lean route unavailable')
    return m.Runtime(tmp_path, lake, lake_bin)


@pytest.mark.parametrize('source,expected,status', [
    (GOLD, True, 'measured'),
    ('import Mathlib\nnamespace Renamed\ndef changed (n : Nat) : Nat := n + 1\nend Renamed\n', True, 'measured'),
    ('import Mathlib\ndef increment (n : Nat) : Nat := n\n', False, 'measured'),
    ('import Mathlib\ndef increment : String := "other type"\n', None, 'incomplete'),
    ('import Mathlib\ndef increment (n : Nat) : Nat := missingSymbol\n', False, 'compile_failure'),
])
def test_authored_hidden_outcomes(tmp_path, source, expected, status):
    result = runtime(tmp_path).evaluate(extract(GOLD), source, 'E13Hidden'+'0'*24)
    assert result['hidden_all_pass'] is expected
    assert result['status'] == status
    if status == 'incomplete':
        assert result['n_unmapped'] == 1 and result['n_evaluable'] == 0


def test_real_agreement_probe_uses_arguments_without_expected_values(tmp_path):
    gold = 'def original (n : Nat) : Nat := 99999\nexample : original 2 = 99999 := rfl\n'
    candidate = 'import Mathlib\ndef alpha (n : Nat) : Nat := n + 1\ndef beta (n : Nat) : Nat := 1 + n\n'
    result = runtime(tmp_path).evaluate(extract(gold), candidate, 'E13Hidden'+'1'*24)
    assert result['diagnostics'][0]['step'] == 3
    assert result['hidden_all_pass'] is False
    probes = list(tmp_path.glob('*_Agreement_*.lean'))
    assert len(probes) == 1 and '99999' not in probes[0].read_text()
    assert '(2)' in probes[0].read_text()


def test_selected_compiling_mutant_reuses_exact_module(tmp_path, monkeypatch):
    r = runtime(tmp_path)
    source = 'import Mathlib\ndef increment (n : Nat) : Nat := n\n'
    module = 'E13Hidden'+'4'*24
    _, receipt = r.compile(source, module)
    assert receipt['status'] == 'ok'
    monkeypatch.setattr(r, 'compile', lambda *_: pytest.fail('selected mutant recompiled'))
    value = r.evaluate(extract(GOLD), source, module, receipt)
    assert value['hidden_all_pass'] is False
    with pytest.raises(ValueError, match='does not match'):
        r.evaluate(extract(GOLD), source+'\n', module, receipt)


def test_partial_type_unknown_is_not_silently_zero(tmp_path, monkeypatch):
    r = m.Runtime(tmp_path, '/unused', '/unused')
    suite = extract(GOLD + 'example : increment 3 = 4 := rfl\n')
    monkeypatch.setattr(r, 'compile', lambda *_: (tmp_path/'unused', {'status': 'ok'}))
    monkeypatch.setattr(r, 'lean', lambda *_: {'status': 'error', 'outputs': {0: True}})
    value = r.evaluate(suite, GOLD, 'E13Hidden'+'2'*24)
    assert value['status'] == 'incomplete' and value['hidden_all_pass'] is None
    assert value['hidden_pass_rate'] == 1 and value['n_type_unknown'] == 1
    assert [x['status'] for x in value['per_test']] == ['pass', 'type_unknown']


def test_compile_timeout_is_missing_not_failure(tmp_path, monkeypatch):
    r = m.Runtime(tmp_path, '/unused', '/unused')
    monkeypatch.setattr(r, 'compile', lambda *_: (tmp_path/'unused', {'status': 'timeout'}))
    value = r.evaluate(extract(GOLD), GOLD, 'E13Hidden'+'3'*24)
    assert value['status'] == 'unresolved_compile' and value['hidden_all_pass'] is None
    assert value['hidden_pass_rate'] is None


def fixture(tmp_path):
    train = tmp_path/'train.txt'; train.write_text('authored\n')
    source = tmp_path/'source.lean'; source.write_text(GOLD)
    suite = tmp_path/'suite.json'; suite.write_text(json.dumps(extract(GOLD)))
    cell = {'cell_id': 'authored/control', 'task_id': 'authored', 'split': 'train',
            'source': str(source), 'suite': str(suite)}
    config = {'train_ids': str(train), 'root': str(tmp_path/'results'), 'lake': '/unused', 'lake_bin': '/unused'}
    bound = {str(p): m.digest(p) for p in (train, source, suite)}
    return cell, config, bound


def test_durable_cell_recovery_and_changed_inputs(tmp_path):
    cell, config, bound = fixture(tmp_path)
    calls = []
    class Fake:
        def __init__(self, *args): pass
        def evaluate(self, *args):
            calls.append(args)
            return {'status': 'measured', 'hidden_all_pass': True}
    first = m.measure_cell(cell, config, bound, 'fixed', Fake)
    assert m.measure_cell(cell, config, bound, 'fixed', Fake) == first
    assert len(calls) == 1
    with pytest.raises(ValueError, match='binding changed'):
        m.measure_cell(cell, config, bound, 'changed', Fake)
    Path(cell['source']).write_text(GOLD+'\n')
    with pytest.raises(ValueError, match='unbound or changed'):
        m.measure_cell(cell, config, bound, 'fixed', Fake)


def test_heldout_refused_before_read_and_incomplete_attempt_never_retried(tmp_path):
    cell, config, bound = fixture(tmp_path)
    cell['split'] = 'test'; cell['source'] = '/must-not-read'
    with pytest.raises(ValueError, match='train cells'):
        m.measure_cell(cell, config, bound, 'fixed')
    cell['split'] = 'train'; cell['source'] = str(tmp_path/'source.lean')
    class Failed:
        def __init__(self, *args): pass
        def evaluate(self, *args): raise OSError('authored process failure')
    with pytest.raises(OSError): m.measure_cell(cell, config, bound, 'fixed', Failed)
    with pytest.raises(RuntimeError, match='never implicitly rerun'):
        m.measure_cell(cell, config, bound, 'fixed', Failed)
