import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x + y
theorem spec_commutative (x y : Int) : solution x y = solution y x := by
  simp [solution, add_comm]
theorem test_positive : solution 2 3 = 5 := by decide
theorem test_negative : solution (-3) 1 = -2 := by decide
end Tiny
