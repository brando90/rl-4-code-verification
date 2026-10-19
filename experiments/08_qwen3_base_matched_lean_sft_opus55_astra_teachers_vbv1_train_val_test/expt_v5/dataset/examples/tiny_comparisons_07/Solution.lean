import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x < y ∧ y < z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x < y ∧ y < z := by
  simp [solution]

theorem test_increasing : solution (-1) 0 2 = true := by
  decide

theorem test_equal_end : solution 1 2 2 = false := by
  decide

end Tiny
