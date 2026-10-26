import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (x < y)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ x < y := by
  simp [solution]

theorem test_increasing : solution 2 3 = true := by
  decide

theorem test_equal : solution (-4) (-4) = false := by
  decide

end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_increasing
#print axioms Tiny.test_equal
