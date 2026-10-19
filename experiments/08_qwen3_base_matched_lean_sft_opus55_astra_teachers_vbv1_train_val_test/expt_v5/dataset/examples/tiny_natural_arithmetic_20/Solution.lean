import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x - min y z
theorem spec_first (x y z : Nat) (h : y ≤ z) : solution x y z = x - y := by
  simp [solution, h]
theorem test_positive : solution 10 3 6 = 7 := by norm_num [solution]
theorem test_clamped : solution 3 4 1 = 2 := by norm_num [solution]
end Tiny
