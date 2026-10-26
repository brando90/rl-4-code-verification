import Mathlib
namespace Tiny
def solution (x y : Nat) : Nat := x - y
theorem spec_zero_iff (x y : Nat) : solution x y = 0 ↔ x ≤ y := by
  exact Nat.sub_eq_zero_iff_le
theorem test_positive : solution 7 3 = 4 := by norm_num [solution]
theorem test_clamped : solution 3 7 = 0 := by norm_num [solution]
end Tiny
