import Mathlib
namespace Tiny
def solution (x : Nat) : Nat := x ^ 2
theorem spec_product (x : Nat) : solution x = x * x := by
  simp [solution, pow_two]
theorem test_small : solution 5 = 25 := by norm_num [solution]
theorem test_zero : solution 0 = 0 := by norm_num [solution]
end Tiny
