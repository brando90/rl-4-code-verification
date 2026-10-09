"""Check extraction and mapping boundaries, including indistinguishable renamed implementations."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from extract_hidden_tests import extract, strip_comments
from adapter_e12 import map_symbols, repoint, renamed_control, signature

GOLD='''import Mathlib
namespace Original
def f (x : Nat) : Bool := decide (x = 1)
def fImp (x : Nat) : Bool := Id.run do return decide (x = 1)
example : f 1 = true := by native_decide
example : fImp 0 = false := by native_decide
example (x : Nat) : f x = f x := rfl
example : ∀ x, f x = f x := by intro x; rfl
end Original
'''


def test_only_closed_examples_and_no_comment_ghosts():
    result=extract('/- /- nested -/ example : fake 1 = 0 := rfl -/\n'+GOLD)
    assert result['n_tests']==2
    assert {s['full_name'] for s in result['symbols']}=={'Original.f','Original.fImp'}


def test_comment_stripper_preserves_string_and_newlines():
    source='def s := "-- /- keep -/"\n/- discard\n/- nested -/ -/\n'
    clean=strip_comments(source)
    assert '"-- /- keep -/"' in clean
    assert len(clean)==len(source) and clean.count('\n')==source.count('\n')
    assert 'discard' not in clean


def test_gold_self_mapping_and_namespace_normalization():
    suite=extract(GOLD)
    mapping,diag=map_symbols(suite['symbols'],GOLD.replace('Original','Candidate'))
    assert mapping=={'Original.f':'Candidate.f','Original.fImp':'Candidate.fImp'}
    assert repoint(suite['tests'][0],mapping)=='_root_.Candidate.f 1 = true'


def test_unique_compatible_explicit_type_mapping():
    suite=extract('def f (x : Nat) : Bool := x == 1\nexample : f 1 = true := by decide\n')
    mapping,_=map_symbols(suite['symbols'],'def other (value : Int) : Bool := value == 1\n')
    assert mapping=={'f':'other'}
    assert signature('(x y : Nat) : Bool')==(('NUM','NUM'),'Bool')


def test_renamed_twins_are_ambiguous_not_arbitrarily_assigned():
    suite=extract(GOLD);candidate,_=renamed_control(GOLD,suite['symbols'])
    mapping,diag=map_symbols(suite['symbols'],candidate)
    assert mapping=={}
    assert len(diag)==2 and all(d['status']=='ambiguous' and len(d['candidates'])==2 for d in diag)
    assert repoint(suite['tests'][0],mapping) is None


def test_free_section_variables_are_not_hidden_tests():
    suite=extract('variable (x : Nat)\ndef f (n : Nat) : Nat := n\nexample : f x = x := rfl\n')
    assert suite['n_tests']==0


def test_equation_definitions_and_field_projection_repointing():
    source='''namespace N
structure State where
  cycles : Nat
def initState : State := { cycles := 0 }
def count : List Nat → Nat
  | [] => 0
  | _ :: xs => 1 + count xs
example : count [1,2] = 2 := by decide
example : initState.cycles = 0 := rfl
end N
'''
    suite=extract(source)
    assert suite['n_tests']==2
    assert {s['full_name'] for s in suite['symbols']}=={'N.initState','N.count'}
    candidate,_=renamed_control(source,suite['symbols'])
    assert 'e12renamed0000.cycles' in candidate
    mapping,_=map_symbols(suite['symbols'],candidate)
    assert repoint(suite['tests'][1],mapping)=='_root_.N.e12renamed0000.cycles = 0'
    assert signature(': List Nat → Nat')==signature('(xs : List Nat) : Nat')


def test_a2_normalized_name_precedes_type():
    suite=extract('def my_f (x : Nat) : Bool := true\nexample : my_f 1 = true := by decide\n')
    mapping,diag=map_symbols(suite['symbols'],'def MyF (x : Nat) : Bool := false\n')
    assert mapping=={'my_f':'MyF'} and diag[0]['step']==1


def test_a2_agreement_gets_arguments_never_expected_values():
    from adapter_e12 import argument_tuples
    source='def f (xs : List Nat) (s : String) : String := s\nexample : f [1,2] "input" = "EXPECTED_ONLY" := by decide\n'
    suite=extract(source)
    assert argument_tuples(suite['symbols'][0],suite['tests'])==[['[1,2]','"input"']]
    candidate='def a (xs : List Nat) (s : String) : String := s\ndef b (xs : List Nat) (s : String) : String := s\nexample : b [] "x" = "x" := rfl\n'
    calls=[]
    def agree(g,m,t):
        calls.append(t);return {'agrees':True}
    mapping,diag=map_symbols(suite['symbols'],candidate,suite['tests'],agree)
    assert mapping=={'f':'b'} and diag[0]['step']==3
    assert 'EXPECTED_ONLY' not in repr(calls)


def test_a2_disagreement_uses_examples_then_theorems_and_rejects_ties():
    suite=extract('def f (x : Nat) : Bool := true\nexample : f 1 = true := by decide\n')
    source='def a (x : Nat) : Bool := true\ndef b (x : Nat) : Bool := false\n'
    disagree=lambda *_:{'agrees':False}
    mapping,diag=map_symbols(suite['symbols'],source,suite['tests'],disagree)
    assert not mapping and diag[0]['reason']=='ambiguous_disagreeing'
    source+='example : a 1 = true := rfl\nexample : b 1 = false := rfl\ntheorem selected : b 0 = false := rfl\n'
    mapping,diag=map_symbols(suite['symbols'],source,suite['tests'],disagree)
    assert mapping=={'f':'b'} and diag[0]['step']==4


def test_mutation_keeps_only_one_body_token_change_and_removes_old_assertions():
    from controls_e12 import remove_propositions,mutations
    suite=extract(GOLD);stripped=remove_propositions(GOLD)
    assert 'example' not in stripped and 'def fImp' in stripped and 'end Original' in stripped
    changed,receipt=next(mutations(stripped,suite['symbols']))
    a=receipt['offset'];old=receipt['old'];new=receipt['new']
    assert changed==stripped[:a]+new+stripped[a+len(old):]
    assert receipt['definition']=='Original.f'


def test_mutant_copy_has_no_orphan_docstring_before_end():
    from controls_e12 import remove_propositions
    source="namespace N\ndef f (x : Nat) : Bool := true\n/-- Unit check. -/\nexample : f 0 = true := rfl\nend N\n"
    stripped=remove_propositions(source)
    assert '/--' not in stripped and 'example' not in stripped and 'end N' in stripped


def test_argument_arrays_and_field_suffixes():
    from adapter_e12 import atom_at
    assert atom_at('#[1, 2].toList 7',0)==('#[1, 2].toList',14)
    assert atom_at('[1, 2].reverse 7',0)==('[1, 2].reverse',14)
