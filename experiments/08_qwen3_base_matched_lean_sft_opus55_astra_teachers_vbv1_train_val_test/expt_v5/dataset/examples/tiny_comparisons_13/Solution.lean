import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (x ≤ y ∨ y ≤ x)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ x ≤ y ∨ y ≤ x := by
  simp [solution]

theorem test_forward : solution (-3) 1 = true := by
  decide

theorem test_reverse : solution 4 (-2) = true := by
  decide

end Tiny
