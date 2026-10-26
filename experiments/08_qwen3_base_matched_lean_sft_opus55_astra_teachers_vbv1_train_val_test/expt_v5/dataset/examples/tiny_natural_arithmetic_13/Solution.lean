import Mathlib
namespace Tiny
def solution (x y : Nat) : Nat := (x + y) ^ 2
theorem spec_expand (x y : Nat) : solution x y = x * x + 2 * x * y + y * y := by
  simp only [solution, pow_two]
  ring
theorem test_small : solution 2 3 = 25 := by norm_num [solution]
theorem test_zero : solution 0 5 = 25 := by norm_num [solution]
end Tiny
