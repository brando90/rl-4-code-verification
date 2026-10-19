import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x - x * y
theorem spec_factored (x y : Int) : solution x y = x * (1 - y) := by
  simp only [solution]
  ring
theorem test_positive : solution 5 2 = -5 := by norm_num [solution]
theorem test_negative : solution (-3) 2 = 3 := by norm_num [solution]
end Tiny
