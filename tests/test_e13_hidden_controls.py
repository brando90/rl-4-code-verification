"""Keep hidden-control thresholds fixed and choose mutants solely by compilation."""
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_hidden_controls', PHASE/'hidden_controls.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def rows():
    good = {'status': 'measured', 'compile': {'status': 'ok'}, 'n_pass': 100, 'n_evaluable': 100,
            'n_mapped': 100, 'hidden_all_pass': True}
    bad = {**good, 'n_pass': 99, 'hidden_all_pass': False}
    return [{'task_id': 'authored'+str(i), 'n_tests': 100, 'C1': dict(good), 'C2': dict(good),
             'C3': dict(bad), 'C4': dict(bad)} for i in range(64)]


def test_all_frozen_control_boundaries_and_denominators():
    data = rows()
    for row in data[:2]: row['C1'].update(n_pass=36, hidden_all_pass=False)
    for row in data[2:5]: row['C2']['hidden_all_pass'] = False
    for row in data[:25]: row['C3']['n_pass'] = 100
    for row in data[:3]: row['C4']['n_pass'] = 100
    assert m.summarize(data)['status'] == 'PASS'
    data[5]['C2']['hidden_all_pass'] = False
    assert not m.summarize(data)['controls']['C2']['pass']
    data = rows()
    for row in data[:15]: row['C3'] = {'status': 'no_compiling_mutant'}
    result = m.summarize(data)
    assert result['controls']['C3']['compiling_mutants'] == 49
    assert not result['controls']['C3']['pass']
    assert result['cell_status_counts']['C3']['no_compiling_mutant'] == 15
    with pytest.raises(ValueError, match='denominator'): m.summarize(data[:-1])
    with pytest.raises(ValueError, match='duplicated'): m.summarize([data[0]]*64)


def test_unknown_wrong_task_bridge_is_not_accepted_as_a_rejection():
    data = rows()
    for row in data:
        row['C4'] = {'status': 'incomplete', 'compile': {'status': 'ok'}, 'n_mapped': 100,
                     'n_evaluable': 0, 'n_pass': 0, 'n_type_unknown': 100}
    result = m.summarize(data)
    assert result['controls']['C4']['rejected_or_failing'] == 0
    assert result['per_test_unknown_counts']['C4'] == 6400
    assert result['status'] == 'FAIL'


def test_mutant_first_compile_is_used_even_when_it_survives(tmp_path, monkeypatch):
    import contextlib, json
    suite = tmp_path/'suite.json'; suite.write_text(json.dumps({'n_tests': 1}))
    paths = {}
    for kind in ('C1', 'C2', 'C4', 'C3_00', 'C3_01', 'C3_02'):
        p = tmp_path/(kind+'.lean'); p.write_text(kind); paths[kind] = str(p)
    row = {'index': 0, 'task_id': 'authored', 'suite': str(suite), 'n_tests': 1,
           'sources': paths, 'mutants': [{'kind': k} for k in ('C3_00', 'C3_01', 'C3_02')]}
    calls = []
    class Runtime:
        def __init__(self, *args): pass
        def compile(self, source, module):
            calls.append(source)
            return None, {'status': 'error' if source == 'C3_00' else 'ok'}
        def evaluate(self, suite, source, module, compiled=None):
            return {'status': 'measured', 'compile': compiled or {'status': 'ok'}, 'hidden_all_pass': True}
    monkeypatch.setattr(m, 'Runtime', Runtime)
    result = m.evaluate_task(row, {'work': str(tmp_path), 'lake': '/unused', 'lake_bin': '/unused'}, contextlib.nullcontext())
    assert calls == ['C3_00', 'C3_01']
    assert result['C3']['hidden_all_pass'] is True and result['C3']['mutation']['kind'] == 'C3_01'
