import Mathlib
namespace Tiny
def solution (x : Nat) : Nat := x * (x + 1)
theorem spec_expand (x : Nat) : solution x = x * x + x := by
  simp [solution, Nat.mul_add]
theorem test_small : solution 4 = 20 := by norm_num [solution]
theorem test_zero : solution 0 = 0 := by norm_num [solution]
end Tiny
