import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x + y ≤ z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x + y ≤ z := by
  simp [solution]

theorem test_equal_sum : solution 2 3 5 = true := by
  decide

theorem test_too_large : solution (-1) 4 2 = false := by
  decide

end Tiny
