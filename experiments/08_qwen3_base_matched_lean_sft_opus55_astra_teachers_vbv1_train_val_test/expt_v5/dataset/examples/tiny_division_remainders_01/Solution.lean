import Mathlib
namespace Tiny
def solution (x : Int) : Int := x / 2
theorem spec_double (x : Int) : solution (2 * x) = x := by simp [solution]
theorem test_negative : solution (-3) = -2 := by norm_num [solution]
theorem test_positive : solution 7 = 3 := by norm_num [solution]
end Tiny
