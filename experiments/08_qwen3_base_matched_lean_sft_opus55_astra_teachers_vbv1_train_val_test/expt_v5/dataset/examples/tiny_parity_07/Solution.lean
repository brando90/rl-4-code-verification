import Mathlib
namespace Tiny
def solution (x y : Int) : Bool := (x * y) % 2 != 0
theorem spec_commutative (x y : Int) : solution x y = solution y x := by simp [solution, mul_comm]
theorem test_odd_product : solution 3 (-5) = true := by decide
theorem test_even_product : solution 2 7 = false := by decide
end Tiny
