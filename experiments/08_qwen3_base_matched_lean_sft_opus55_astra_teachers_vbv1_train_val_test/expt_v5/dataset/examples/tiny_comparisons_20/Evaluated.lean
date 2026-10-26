import Mathlib

namespace Tiny

def solution (x : Int) : Bool := decide (x * x ≥ 0)

theorem spec_true_iff (x : Int) : solution x = true ↔ x * x ≥ 0 := by
  simp [solution]

theorem test_negative : solution (-4) = true := by
  decide

theorem test_zero : solution 0 = true := by
  decide

end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_negative
#print axioms Tiny.test_zero
