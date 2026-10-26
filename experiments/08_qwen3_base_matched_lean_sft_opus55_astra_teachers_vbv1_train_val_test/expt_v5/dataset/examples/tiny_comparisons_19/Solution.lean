import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (|x| ≤ y)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ |x| ≤ y := by
  simp [solution]

theorem test_enough : solution (-3) 3 = true := by
  decide

theorem test_too_small : solution (-3) 2 = false := by
  decide

end Tiny
