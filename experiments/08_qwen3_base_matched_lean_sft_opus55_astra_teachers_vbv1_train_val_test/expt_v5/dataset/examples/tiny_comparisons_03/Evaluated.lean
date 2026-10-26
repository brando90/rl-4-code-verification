import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (x = y)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ x = y := by
  simp [solution]

theorem test_same : solution (-3) (-3) = true := by
  decide

theorem test_different : solution 2 3 = false := by
  decide

end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_same
#print axioms Tiny.test_different
