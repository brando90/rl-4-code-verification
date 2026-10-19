import Mathlib
namespace Tiny
def solution (p q : Bool) : Bool := (p && !q) || (!p && q)
theorem spec_inequality (p q : Bool) : solution p q = !(p == q) := by
  cases p <;> cases q <;> decide
theorem test_same : solution false false = false := by decide
theorem test_different : solution false true = true := by decide
end Tiny
