import Mathlib
namespace Tiny
def solution (p q r : Bool) : Bool := p && (q || r)
theorem spec_distribute (p q r : Bool) : solution p q r = (p && q) || (p && r) := by
  cases p <;> cases q <;> cases r <;> decide
theorem test_true_false_true : solution true false true = true := by decide
theorem test_false_true_true : solution false true true = false := by decide
end Tiny
#print axioms Tiny.spec_distribute
#print axioms Tiny.test_true_false_true
#print axioms Tiny.test_false_true_true
