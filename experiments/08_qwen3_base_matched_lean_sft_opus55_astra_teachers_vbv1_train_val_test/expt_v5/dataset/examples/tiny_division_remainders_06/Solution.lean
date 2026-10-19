import Mathlib
namespace Tiny
def solution (x : Int) : Int := x % 4
theorem spec_multiple (x : Int) : solution (4 * x) = 0 := by simp [solution]
theorem test_negative : solution (-7) = 1 := by norm_num [solution]
theorem test_positive : solution 9 = 1 := by norm_num [solution]
end Tiny
