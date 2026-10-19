import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (x ≤ y)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ x ≤ y := by
  simp [solution]

theorem test_less : solution (-2) 3 = true := by
  decide

theorem test_greater : solution 5 4 = false := by
  decide

end Tiny
