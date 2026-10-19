import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : Int × Int := (x / (n + 1), x % (n + 1))
theorem spec_zero (n : Nat) : solution 0 n = (0, 0) := by simp [solution]
theorem test_negative : solution (-7) 2 = (-3, 2) := by norm_num [solution]
theorem test_positive : solution 8 2 = (2, 2) := by norm_num [solution]
end Tiny
