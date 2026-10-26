import Mathlib
namespace Tiny
def solution (x y : Nat) : Nat := x * y
theorem spec_commutative (x y : Nat) : solution x y = solution y x := by
  simp [solution, Nat.mul_comm]
theorem test_small : solution 3 4 = 12 := by norm_num [solution]
theorem test_zero : solution 0 7 = 0 := by norm_num [solution]
end Tiny
