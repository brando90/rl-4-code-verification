"""Check experiment 12 version 2's corrected lexer, entry-point priority order and per-test applicability on synthetic identifiers, the 20 inspected disagreement skeletons and the version-1 control fixtures."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
E12 = ROOT / 'experiments' / '12_scsc_vs_hidden_gold_tests_vbv1_across_systems'
sys.path.insert(0, str(E12 / 'expt_v2' / 'scripts'))
sys.path.insert(0, str(E12 / 'expt_v1' / 'scripts'))
import adapter_v2 as v2  # noqa: E402
from extract_hidden_tests import extract  # noqa: E402  (frozen version-1 extractor, read-only)

FIXTURES = json.loads((E12 / 'expt_v2' / 'fixtures' / 'disagreement_skeletons_e12v2.json').read_text())
BY_TASK = {(r['system'], r['task_id']): r for r in FIXTURES}


# ----------------------------------------------------------------- lexer
@pytest.mark.parametrize('text,tokens', [
    ('canFree? 0 = some true', ['canFree?', 'some', 'true']),
    ('xs.get! 2', ['xs.get!', '2']),
    ('a?b', ['a?b']),
    ('«weird name».run 1', ['«weird name».run', '1']),
    ('Foo.Bar.baz', ['Foo.Bar.baz']),
    ('p.1 + q.2', ['p.1', 'q.2']),
    ('x₁ + α', ['x₁', 'α']),
    ('⟨?_, h⟩', ['h']),
    ('¬ (f [2, 4, 6] > 1)', ['f']),
    ('f x != y', ['f', 'x', 'y']),
])
def test_lexer_matches_lean_identifier_grammar(text, tokens):
    found = [t for t in v2.IDENT.findall(text) if not t.isdigit()]
    assert found == [t for t in tokens if not t.isdigit()]


def test_question_mark_definitions_are_distinct_declarations():
    src = 'namespace N\ndef canFree (p : Int) : Bool := p == 0\ndef canFree? (p : Int) : Option Bool := some (canFree p)\nend N\n'
    defs, _, counts = v2.declarations(src)
    assert [d['full_name'] for d in defs] == ['N.canFree', 'N.canFree?']
    assert defs[1]['header'] == '(p : Int) : Option Bool'
    assert v2.signature(defs[1]['header']) == {'args': ('NUM',), 'result': 'Option Bool', 'arity': 1, 'has_implicit': False}
    assert counts == {'n_examples': 0, 'n_eval_commands': 0}


def test_reference_counts_no_longer_collapse_suffixed_wrappers():
    src = ('def core (p : Int) : Bool := true\ndef core? (p : Int) : Option Bool := some true\ndef helper (p : Int) : Bool := true\n'
           'example : core 1 = true := rfl\nexample : core? 1 = some true := rfl\nexample : helper 1 = true := rfl\ntheorem t : core 2 = true := rfl\n')
    defs, _, _ = v2.declarations(src)
    counts = v2.reference_counts(src, defs)
    assert counts == {'core': [1, 1], 'core?': [1, 0], 'helper': [1, 0]}


@pytest.mark.parametrize('name,helper', [
    ('preCondition', True), ('preCondB', True), ('PostB', True), ('postCheck', True), ('Pre', True), ('pre_cond', True),
    ('PreCrossCheckB', True), ('spec_prop', True), ('checkHarness', True), ('greatestCheck', True),
    ('prefixSum', False), ('predict', False), ('postpone', False), ('gate', False), ('canFree', False), ('pickLeftImp', False),
])
def test_helper_name_rule(name, helper):
    assert v2.is_helper(name) is helper


def test_implicit_binders_are_skipped_not_fatal():
    sig = v2.signature('{α : Type} (url : List α) (bufSize : Nat) : Bool')
    assert sig['arity'] == 2 and sig['has_implicit'] and sig['args'] == ('List i0', 'NUM')
    assert v2.signature(': Nat → Nat → Nat')['arity'] == 2


# ------------------------------------------------- the 20 inspected rows
def run_fixture(system, task, agreement=None):
    row = BY_TASK[(system, task)]
    mapping, diag, summary = v2.map_symbols(row['gold_symbols'], row['candidate_skeleton'], row['gold_tests'], agreement)
    return row, mapping, {d['gold_symbol']: d for d in diag}, summary


def test_fixture_file_covers_all_twenty_inspected_rows():
    assert len(FIXTURES) == 20
    assert sum(r['group'] == 'high_score_failing' for r in FIXTURES) == 10
    assert all('sorry' not in r['candidate_skeleton'] for r in FIXTURES)


def test_hazard_pointer_selects_core_not_precondition_or_option_wrapper():
    row, mapping, diag, _ = run_fixture('claude-opus-5-max', 'concurrent_set_synthetic__my_hazard_pointer_can_free')
    assert mapping == {'MyHazardPointerCanFree.MyHazardPointerCanFree': 'MyHazardPointerCanFree.canFree',
                       'MyHazardPointerCanFree.MyHazardPointerCanFreeImp': 'MyHazardPointerCanFree.canFree'}
    d = diag['MyHazardPointerCanFree.MyHazardPointerCanFree']
    assert d['step'] == '2b' and 'MyHazardPointerCanFree.preCondition' in d['helpers_excluded']
    assert row['v1_mapping']['MyHazardPointerCanFree.MyHazardPointerCanFree'] == 'MyHazardPointerCanFree.preCondition'


def test_lww_pick_left_opus_prefers_affine_core_and_probes_twins():
    _, mapping, diag, _ = run_fixture('claude-opus-5-max', 'concurrent_set_synthetic__my_lww_register_pick_left')
    assert mapping == {'MyLwwRegisterPickLeft.MyLwwRegisterPickLeft': 'MyLwwRegisterPickLeft.pickLeft'}
    imp = diag['MyLwwRegisterPickLeft.MyLwwRegisterPickLeftImp']
    assert imp['status'] == 'needs_probe' and set(imp['candidates']) == {'MyLwwRegisterPickLeft.pickLeft', 'MyLwwRegisterPickLeft.pickLeftImp'}
    assert 'MyLwwRegisterPickLeft.preCondition' not in imp['candidates']
    _, mapping, diag, _ = run_fixture('claude-opus-5-max', 'concurrent_set_synthetic__my_lww_register_pick_left', lambda g, m, t: {'agrees': True})
    assert mapping['MyLwwRegisterPickLeft.MyLwwRegisterPickLeftImp'] == 'MyLwwRegisterPickLeft.pickLeft'
    assert diag['MyLwwRegisterPickLeft.MyLwwRegisterPickLeftImp']['step'] == 3


@pytest.mark.parametrize('task,expected', [
    ('hypervisor_set_synthetic__my_interrupt_route', {'MyInterruptRoute.myInterruptRoute': 'MyInterruptRoute.myInterruptRoute',
                                                       'MyInterruptRoute.myInterruptRouteImp': 'MyInterruptRoute.myInterruptRouteImp'}),
    ('memory_bugs_set_synthetic__my_bump_alloc_fits', {'MyBumpAllocFits.my_bump_alloc_fits': 'MyBumpAllocFits.myBumpAllocFits',
                                                        'MyBumpAllocFits.my_bump_alloc_fitsImp': 'MyBumpAllocFits.myBumpAllocFitsImp'}),
    ('os_embedded_set_synthetic__my_power_transition_ok', {'MyPowerTransitionOk.myPowerTransitionOk': 'MyPowerTransitionOk.myPowerTransitionOk',
                                                            'MyPowerTransitionOk.myPowerTransitionOkImp': 'MyPowerTransitionOk.myPowerTransitionOkImp'}),
])
def test_suffixed_wrapper_collisions_now_map_by_name_at_step_1(task, expected):
    row, mapping, diag, _ = run_fixture('claude-opus-5-max', task)
    assert mapping == expected
    assert all(d['step'] == 1 and d['result_type_compatible'] for d in diag.values())
    assert set(row['v1_mapping'].values()) != set(expected.values())  # version 1 chose a helper


def test_dose_interval_never_selects_post_or_pre_helpers():
    _, mapping, diag, _ = run_fixture('claude-opus-5-max', 'regulated_set_synthetic__my_dose_interval_ok', lambda g, m, t: {'agrees': False})
    for d in diag.values():
        assert d['chosen'] not in ('MyDoseIntervalOk.PostB', 'MyDoseIntervalOk.preCondB', 'MyDoseIntervalOk.PreCrossCheckB')
        assert {'MyDoseIntervalOk.PostB', 'MyDoseIntervalOk.preCondB', 'MyDoseIntervalOk.PreCrossCheckB'} <= set(d['helpers_excluded'])
        assert 'MyDoseIntervalOk.gate' in d['candidates']
    # With disagreeing members and no referencing examples in the skeleton the honest answer is missing, not a helper.
    assert mapping == {} and all(d['reason'] == 'ambiguous_disagreeing' for d in diag.values())


@pytest.mark.parametrize('task,symbol,flag', [
    ('easy_set__1_myadd', 'MyAdd.myAdd', 'result_type_compatible'),
    ('easy_set__33_myminimum', 'MyMinList.myMinList', 'result_type_compatible'),
    ('humaneval_set__humaneval_22_filter_integers', 'FilterIntegers.filter_integers', 'argument_types_compatible'),
    ('security_set__security_6858__safe__104_unsafehttpparse_safe', 'SafeHttpParse.safeHttpParse', 'argument_types_compatible'),
])
def test_partial_applicability_rows_keep_name_mapping_and_flag_type_mismatch(task, symbol, flag):
    row, mapping, diag, _ = run_fixture('claude-opus-5-max', task)
    assert mapping[symbol] == row['v1_mapping'][symbol]
    assert diag[symbol]['step'] == 1 and diag[symbol][flag] is False


def test_myminimum_imperative_twin_maps_to_unique_scalar_definition():
    _, mapping, diag, _ = run_fixture('claude-opus-5-max', 'easy_set__33_myminimum')
    assert mapping['MyMinList.myMinListImperative'] == 'MyMinimum.minList' and diag['MyMinList.myMinListImperative']['step'] == '2a'


def test_low_score_passing_rows_keep_v1_mapping_and_record_zero_self_tests():
    for row in FIXTURES:
        if row['group'] != 'low_score_passing':
            continue
        _, mapping, diag, summary = run_fixture(row['system'], row['task_id'])
        assert mapping == row['v1_mapping'], row['task_id']
        assert all(d['step'] in (1, '2a') for d in diag.values()), row['task_id']
        assert summary['n_examples'] == 0 and row['candidate_n_examples'] == 0


# ------------------------------------------------- per-test applicability
def test_cell_outcome_reports_partial_applicability_per_test_not_as_failure():
    tests = [{'statement': 'f 1 = 1', 'symbols': {'f': 'f'}}, {'statement': 'g 1 = 1', 'symbols': {'g': 'g'}}, {'statement': 'f 2 = 2', 'symbols': {'f': 'f'}}]
    plan = v2.per_test_plan(tests, {'f': 'c.f'})
    assert [r['status'] for r in plan] == ['mapped', 'unmapped', 'mapped']
    out = v2.cell_outcome(3, {0: True}, plan)
    assert out['n_mapped'] == 2 and out['n_evaluable'] == 1 and out['n_type_unknown'] == 1 and out['n_unmapped'] == 1
    assert out['applicable'] and not out['fully_applicable'] and out['hidden_all_pass'] is None
    assert out['hidden_all_evaluable_pass'] is True and out['hidden_pass_rate'] == 1.0
    assert [r['status'] for r in out['per_test']] == ['pass', 'unmapped', 'type_unknown']
    full = v2.cell_outcome(1, {0: False}, v2.per_test_plan(tests[:1], {'f': 'c.f'}))
    assert full['fully_applicable'] and full['hidden_all_pass'] is False


def test_bridge_keeps_version_1_marker_format():
    tests = [{'statement': 'canFree? 1 = some true', 'symbols': {'canFree?': 'N.canFree?'}, 'symbol_suffixes': {'canFree?': ''}}]
    text = v2.bridge('Mod', tests, {'N.canFree?': 'C.canFree?'})
    assert '#eval IO.println ("E12_TEST_0=" ++ toString (decide (_root_.C.canFree? 1 = some true)))' in text


# ------------------------------------------------- version-1 control fixtures
GOLD = '''import Mathlib
namespace Original
def f (x : Nat) : Bool := decide (x = 1)
def fImp (x : Nat) : Bool := Id.run do return decide (x = 1)
example : f 1 = true := by native_decide
example : fImp 0 = false := by native_decide
end Original
'''


def test_v1_control_gold_self_mapping_and_namespace_normalization():
    suite = extract(GOLD)
    mapping, diag, _ = v2.map_symbols(suite['symbols'], GOLD.replace('Original', 'Candidate'))
    assert mapping == {'Original.f': 'Candidate.f', 'Original.fImp': 'Candidate.fImp'}
    assert v2.repoint(suite['tests'][0], mapping) == '_root_.Candidate.f 1 = true'


def test_v1_control_unique_compatible_type_and_renamed_twins_need_probe():
    suite = extract('def f (x : Nat) : Bool := x == 1\nexample : f 1 = true := by decide\n')
    mapping, diag, _ = v2.map_symbols(suite['symbols'], 'def other (value : Int) : Bool := value == 1\n')
    assert mapping == {'f': 'other'} and diag[0]['step'] == '2a'
    from adapter_e12 import renamed_control
    suite = extract(GOLD)
    candidate, _ = renamed_control(GOLD, suite['symbols'])
    mapping, diag, _ = v2.map_symbols(suite['symbols'], candidate)
    assert mapping == {} and all(d['status'] == 'needs_probe' and len(d['candidates']) == 2 for d in diag)
    mapping, diag, _ = v2.map_symbols(suite['symbols'], candidate, suite['tests'], lambda g, m, t: {'agrees': True})
    assert set(mapping) == {'Original.f', 'Original.fImp'} and all(d['step'] == 3 for d in diag)


def test_v1_control_disagreement_uses_examples_then_theorems_and_rejects_ties():
    suite = extract('def f (x : Nat) : Bool := true\nexample : f 1 = true := by decide\n')
    source = 'def a (x : Nat) : Bool := true\ndef b (x : Nat) : Bool := false\n'
    disagree = lambda *_: {'agrees': False}  # noqa: E731
    mapping, diag, _ = v2.map_symbols(suite['symbols'], source, suite['tests'], disagree)
    assert not mapping and diag[0]['reason'] == 'ambiguous_disagreeing'
    source += 'example : a 1 = true := rfl\nexample : b 1 = false := rfl\ntheorem selected : b 0 = false := rfl\n'
    mapping, diag, _ = v2.map_symbols(suite['symbols'], source, suite['tests'], disagree)
    assert mapping == {'f': 'b'} and diag[0]['step'] == 4


def test_same_name_different_arity_is_not_the_entry_point():
    suite = extract('def f (x : Nat) : Bool := true\nexample : f 1 = true := by decide\n')
    mapping, diag, _ = v2.map_symbols(suite['symbols'], 'def f (x y : Nat) : Bool := true\ndef g (x : Nat) : Bool := true\n')
    assert mapping == {'f': 'g'} and diag[0]['step'] == '2a' and diag[0]['reason'] is None


def test_agreement_probe_receives_arguments_never_expected_values():
    source = 'def f (xs : List Nat) (s : String) : String := s\nexample : f [1,2] "input" = "EXPECTED_ONLY" := by decide\n'
    suite = extract(source)
    candidate = 'def a (xs : List Nat) (s : String) : String := s\ndef b (xs : List Nat) (s : String) : String := s\n'
    calls = []

    def agree(g, m, t):
        calls.append(t)
        return {'agrees': True}
    mapping, diag, _ = v2.map_symbols(suite['symbols'], candidate, suite['tests'], agree)
    assert mapping == {'f': 'a'} and calls == [[['[1,2]', '"input"']]] and 'EXPECTED_ONLY' not in repr(calls)
