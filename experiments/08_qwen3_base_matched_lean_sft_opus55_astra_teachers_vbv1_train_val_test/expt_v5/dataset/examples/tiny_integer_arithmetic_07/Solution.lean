import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := x - (y - z)
theorem spec_difference (x y z : Int) : solution x y z - x = z - y := by
  simp [solution]
theorem test_positive : solution 8 5 2 = 5 := by norm_num [solution]
theorem test_negative : solution (-1) 3 (-2) = -6 := by norm_num [solution]
end Tiny
