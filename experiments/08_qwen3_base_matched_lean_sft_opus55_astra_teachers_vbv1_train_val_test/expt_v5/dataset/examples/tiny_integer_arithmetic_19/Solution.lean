import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x * (1 - y)
theorem spec_balance (x y : Int) : solution x y + x * y = x := by
  simp only [solution]
  ring
theorem test_positive : solution 5 2 = -5 := by norm_num [solution]
theorem test_negative : solution (-3) 2 = 3 := by norm_num [solution]
end Tiny
