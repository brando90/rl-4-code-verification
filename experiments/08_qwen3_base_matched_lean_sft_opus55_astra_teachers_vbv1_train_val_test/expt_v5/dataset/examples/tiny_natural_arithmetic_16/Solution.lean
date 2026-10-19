import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x - y - z
theorem spec_combined (x y z : Nat) : solution x y z = x - (y + z) := by
  simp [solution, Nat.sub_sub]
theorem test_positive : solution 10 3 2 = 5 := by norm_num [solution]
theorem test_clamped : solution 3 2 4 = 0 := by norm_num [solution]
end Tiny
