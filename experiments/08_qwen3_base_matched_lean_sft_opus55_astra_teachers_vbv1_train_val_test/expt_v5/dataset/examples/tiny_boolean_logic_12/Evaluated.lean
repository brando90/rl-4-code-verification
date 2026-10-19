import Mathlib
namespace Tiny
def solution (p q r : Bool) : Bool := (p || q) && (p || r)
theorem spec_factor (p q r : Bool) : solution p q r = p || (q && r) := by
  cases p <;> cases q <;> cases r <;> decide
theorem test_false_true_true : solution false true true = true := by decide
theorem test_false_true_false : solution false true false = false := by decide
end Tiny
#print axioms Tiny.spec_factor
#print axioms Tiny.test_false_true_true
#print axioms Tiny.test_false_true_false
