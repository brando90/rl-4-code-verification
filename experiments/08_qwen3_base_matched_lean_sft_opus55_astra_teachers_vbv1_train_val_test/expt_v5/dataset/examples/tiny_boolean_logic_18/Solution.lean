import Mathlib
namespace Tiny
def solution (p q r : Bool) : Bool := (p == q) && (q == r)
theorem spec_endpoints (p q r : Bool) : solution p q r = ((p == q) && (p == r)) := by
  cases p <;> cases q <;> cases r <;> decide
theorem test_all_true : solution true true true = true := by decide
theorem test_one_different : solution true false false = false := by decide
end Tiny
