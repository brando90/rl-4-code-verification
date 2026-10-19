import Mathlib
namespace Tiny
def solution (p q : Bool) : Bool := !(p && q)
theorem spec_de_morgan (p q : Bool) : solution p q = !p || !q := by
  cases p <;> cases q <;> decide
theorem test_true_true : solution true true = false := by decide
theorem test_false_true : solution false true = true := by decide
end Tiny
#print axioms Tiny.spec_de_morgan
#print axioms Tiny.test_true_true
#print axioms Tiny.test_false_true
