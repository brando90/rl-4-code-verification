import Mathlib
namespace Tiny
def solution (x : Int) : Int := x / 5
theorem spec_quintuple (x : Int) : solution (5 * x) = x := by simp [solution]
theorem test_negative : solution (-7) = -2 := by norm_num [solution]
theorem test_positive : solution 11 = 2 := by norm_num [solution]
end Tiny
