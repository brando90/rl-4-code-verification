import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := x * (y - z)
theorem spec_distributive (x y z : Int) : solution x y z = x * y - x * z := by
  simp only [solution]
  ring
theorem test_positive : solution 3 5 2 = 9 := by norm_num [solution]
theorem test_negative : solution (-2) 1 4 = 6 := by norm_num [solution]
end Tiny
