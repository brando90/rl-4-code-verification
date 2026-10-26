import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x * (y + 1)
theorem spec_expand (x y : Int) : solution x y = x * y + x := by
  simp only [solution]
  ring
theorem test_positive : solution 3 4 = 15 := by norm_num [solution]
theorem test_negative : solution (-2) 3 = -8 := by norm_num [solution]
end Tiny
