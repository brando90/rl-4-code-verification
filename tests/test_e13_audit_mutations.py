"""Check byte-accurate audit edits and real Lean reward-gaming counterexamples on authored source."""
import hashlib
import importlib.util
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_audit_mutations', PHASE/'audit_mutations.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture():
    parts = [b'import Mathlib\n', 'def α : Nat := 1\n'.encode(),
             b'theorem first : 1 = 1 := rfl\n', b'theorem second : 2 = 2 := rfl\n', b'#check first\n']
    commands = []; offset = len(parts[0])
    for index, part in enumerate(parts[1:]):
        syntax = {'declaration_kind': m.THEOREM, 'short_name': ('first' if index == 1 else 'second')} if index in (1, 2) else {}
        commands.append({'index': index, 'start': offset, 'stop': offset+len(part), 'syntax': syntax})
        offset += len(part)
    source = b''.join(parts)
    frontend = {'schema': 'e13-declaration-probe-v2', 'terminal': True, 'commands': commands,
                'theorems': [{'command_index': i} for i in (1, 2)]}
    return source, frontend


def test_exact_source_order_and_utf8_preserve_unedited_commands():
    source, frontend = fixture(); saved = bytes(source)
    results = m.construct(source, frontend, expected_sha256=hashlib.sha256(source).hexdigest())
    assert source == saved
    assert results['padding']['source'].startswith(source) and results['padding']['changed_declarations'] == 8
    assert b'theorem first : 1 = 1' in results['deletion']['source']
    assert b'theorem second' not in results['deletion']['source']
    assert 'def α : Nat := 1'.encode() in results['substitution']['source']
    assert b'#check first' in results['substitution']['source']
    assert results['substitution']['source'].count(b'_root_.Nat.add_zero n') == 2
    assert results == m.construct(source, frontend, expected_sha256=hashlib.sha256(source).hexdigest())


def test_no_theorems_is_explicit_and_unknown_spans_are_refused():
    source = b'def value : Nat := 1\n'
    front = {'schema': 'e13-declaration-probe-v2', 'terminal': True, 'commands': [], 'theorems': []}
    values = m.construct(source, front, expected_sha256=hashlib.sha256(source).hexdigest())
    assert values['deletion']['source'] == source and values['deletion']['status'] == 'unchanged_no_named_theorems'
    assert values['substitution']['changed_declarations'] == 0
    with pytest.raises(ValueError, match='source changed'): m.construct(source, front, expected_sha256='0'*64)
    source, front = fixture(); sha = hashlib.sha256(source).hexdigest()
    front['commands'][2]['start'] = 0
    with pytest.raises(ValueError, match='spans'): m.construct(source, front, expected_sha256=sha)


def test_real_frontend_keeps_padding_and_deletion_counterexample(tmp_path):
    lake = os.environ.get('E13_LAKE_DIR')
    if not lake or not Path(lake).exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION') == '1': pytest.fail('required Lean route unavailable')
        pytest.skip('Lean route unavailable')
    sys.path.insert(0, str(PHASE.parent/'R0_attempt_2'))
    from declaration_adapter_v2 import components
    source = (b'import Mathlib\ndef increment (n : Nat) : Nat := n + 1\n'
              b'example : increment 0 = 1 := rfl\n'
              b'theorem correct (n : Nat) : increment n = n + 1 := rfl\n'
              b'theorem unfinished (n : Nat) : increment n > n := by sorry\n')
    path = tmp_path/'original.lean'; path.write_bytes(source)
    before = components(path, lake_dir=lake, evidence=tmp_path/'before')
    assert before['p'] == {'numerator': 1, 'denominator': 2}
    results = m.construct(source, before['raw'], expected_sha256=hashlib.sha256(source).hexdigest())
    for kind, wanted in [('padding', {'numerator': 9, 'denominator': 10}),
                         ('deletion', {'numerator': 1, 'denominator': 1}),
                         ('substitution', {'numerator': 2, 'denominator': 2})]:
        path = tmp_path/(kind+'.lean'); path.write_bytes(results[kind]['source'])
        after = components(path, lake_dir=lake, evidence=tmp_path/kind)
        assert after['p'] == wanted
        assert after['t'] == before['t'] == 1
        assert after['d']['numerator'] == after['d']['denominator']
