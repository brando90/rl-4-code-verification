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
