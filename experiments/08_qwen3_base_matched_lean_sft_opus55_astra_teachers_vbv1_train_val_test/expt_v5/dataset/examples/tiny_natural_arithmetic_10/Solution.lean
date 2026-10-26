import Mathlib
namespace Tiny
def solution (x y : Nat) : Nat := 2 * x + y
theorem spec_reorder (x y : Nat) : solution x y = y + 2 * x := by
  simp [solution, Nat.add_comm]
theorem test_small : solution 3 4 = 10 := by norm_num [solution]
theorem test_zero : solution 0 7 = 7 := by norm_num [solution]
end Tiny
