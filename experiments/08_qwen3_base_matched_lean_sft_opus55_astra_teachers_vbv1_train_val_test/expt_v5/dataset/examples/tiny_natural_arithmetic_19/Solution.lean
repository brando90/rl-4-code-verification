import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x + (y - z)
theorem spec_no_extra (x y z : Nat) (h : y ≤ z) : solution x y z = x := by
  simp [solution, Nat.sub_eq_zero_of_le h]
theorem test_positive : solution 2 7 3 = 6 := by norm_num [solution]
theorem test_clamped : solution 2 3 7 = 2 := by norm_num [solution]
end Tiny
