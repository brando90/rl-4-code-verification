import Mathlib
namespace Tiny
def solution (p q : Bool) : Bool := !p || q
theorem spec_not_counterexample (p q : Bool) : solution p q = !(p && !q) := by
  cases p <;> cases q <;> decide
theorem test_false_false : solution false false = true := by decide
theorem test_true_false : solution true false = false := by decide
end Tiny
