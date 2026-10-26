import Mathlib
namespace Tiny
def solution (p q : Bool) : List Bool := [p, q]
theorem spec_second (p q : Bool) : (solution p q).get? 1 = some q := by simp [solution]
theorem test_true_false : solution true false = [true, false] := by decide
theorem test_false_true : solution false true = [false, true] := by decide
end Tiny
#print axioms Tiny.spec_second
#print axioms Tiny.test_true_false
#print axioms Tiny.test_false_true
