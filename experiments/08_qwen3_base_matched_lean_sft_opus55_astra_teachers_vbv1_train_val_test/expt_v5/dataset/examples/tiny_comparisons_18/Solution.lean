import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x - y < z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x - y < z := by
  simp [solution]

theorem test_true : solution 1 3 (-1) = true := by
  decide

theorem test_equal : solution 5 2 3 = false := by
  decide

end Tiny
