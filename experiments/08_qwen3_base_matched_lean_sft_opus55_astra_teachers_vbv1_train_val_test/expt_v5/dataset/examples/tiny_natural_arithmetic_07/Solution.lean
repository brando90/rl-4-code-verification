import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := (x + y) * z
theorem spec_swap_factor (x y z : Nat) : solution x y z = z * (x + y) := by
  simp [solution, Nat.mul_comm]
theorem test_small : solution 2 3 4 = 20 := by norm_num [solution]
theorem test_zero : solution 2 3 0 = 0 := by norm_num [solution]
end Tiny
