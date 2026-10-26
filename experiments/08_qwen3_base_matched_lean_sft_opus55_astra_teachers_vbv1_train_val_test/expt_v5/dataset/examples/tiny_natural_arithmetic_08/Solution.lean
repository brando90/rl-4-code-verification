import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x * y + z
theorem spec_swap_factors (x y z : Nat) : solution x y z = y * x + z := by
  simp [solution, Nat.mul_comm]
theorem test_small : solution 2 3 4 = 10 := by norm_num [solution]
theorem test_zero : solution 0 3 4 = 4 := by norm_num [solution]
end Tiny
