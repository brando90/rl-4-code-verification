import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : Int := n * x
theorem spec_zero (x : Int) : solution x 0 = 0 := by simp [solution]
theorem spec_step (x : Int) (n : Nat) : solution x (n + 1) = solution x n + x := by
  simp [solution, add_mul]
theorem test_zero : solution 7 0 = 0 := by decide
theorem test_negative : solution (-3) 4 = -12 := by decide
end Tiny
