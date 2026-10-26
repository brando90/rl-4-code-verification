import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x - y
theorem spec_add_right (x y : Int) : solution x y + y = x := by
  simp [solution]
theorem test_positive : solution 7 3 = 4 := by norm_num [solution]
theorem test_negative : solution (-3) 2 = -5 := by norm_num [solution]
end Tiny
