import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x * y
theorem spec_commutative (x y : Int) : solution x y = solution y x := by
  simp [solution, mul_comm]
theorem test_positive : solution 3 4 = 12 := by norm_num [solution]
theorem test_negative : solution (-2) 5 = -10 := by norm_num [solution]
end Tiny
