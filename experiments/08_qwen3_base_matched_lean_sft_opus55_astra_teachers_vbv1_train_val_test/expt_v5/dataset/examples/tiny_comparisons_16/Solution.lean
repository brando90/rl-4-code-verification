import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x ≠ y ∧ y ≠ z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x ≠ y ∧ y ≠ z := by
  simp [solution]

theorem test_all_adjacent_different : solution 1 2 1 = true := by
  decide

theorem test_first_pair_same : solution (-1) (-1) 2 = false := by
  decide

end Tiny
