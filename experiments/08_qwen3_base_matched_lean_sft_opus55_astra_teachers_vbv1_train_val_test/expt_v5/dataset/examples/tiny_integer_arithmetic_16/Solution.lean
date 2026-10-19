import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x + -y
theorem spec_subtract (x y : Int) : solution x y = x - y := by
  simp [solution, sub_eq_add_neg]
theorem test_positive : solution 7 3 = 4 := by norm_num [solution]
theorem test_negative : solution (-3) 2 = -5 := by norm_num [solution]
end Tiny
