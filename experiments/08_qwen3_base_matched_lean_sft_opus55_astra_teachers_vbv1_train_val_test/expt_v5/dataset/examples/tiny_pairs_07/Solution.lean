import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int := pair.1 - pair.2
theorem spec_self (x : Int) : solution (x, x) = 0 := by simp [solution]
theorem test_positive : solution (5, 3) = 2 := by norm_num [solution]
theorem test_negative : solution (-2, 4) = -6 := by norm_num [solution]
end Tiny
