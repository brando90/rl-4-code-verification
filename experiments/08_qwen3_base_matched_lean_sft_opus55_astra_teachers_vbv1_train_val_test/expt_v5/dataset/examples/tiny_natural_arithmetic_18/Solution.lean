import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := max (x + y) z
theorem spec_right_iff (x y z : Nat) : solution x y z = z ↔ x + y ≤ z := by
  simp [solution]
theorem test_sum : solution 2 3 9 = 9 := by norm_num [solution]
theorem test_floor : solution 5 6 7 = 11 := by norm_num [solution]
end Tiny
