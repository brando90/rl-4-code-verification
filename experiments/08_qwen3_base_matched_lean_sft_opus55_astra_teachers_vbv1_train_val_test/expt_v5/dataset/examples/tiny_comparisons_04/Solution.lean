import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (x ≠ y)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ x ≠ y := by
  simp [solution]

theorem test_different : solution (-2) 2 = true := by
  decide

theorem test_same : solution 7 7 = false := by
  decide

end Tiny
