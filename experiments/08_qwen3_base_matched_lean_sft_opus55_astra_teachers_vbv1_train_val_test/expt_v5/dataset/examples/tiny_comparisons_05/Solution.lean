import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (x > y)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ x > y := by
  simp [solution]

theorem test_greater : solution 3 (-1) = true := by
  decide

theorem test_equal : solution 4 4 = false := by
  decide

end Tiny
