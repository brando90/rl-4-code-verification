import Mathlib
namespace Tiny
def solution (x y : Int) : Bool := (x + y) % 2 == 0
theorem spec_commutative (x y : Int) : solution x y = solution y x := by simp [solution, add_comm]
theorem test_even_sum : solution 2 4 = true := by decide
theorem test_odd_sum : solution (-3) 2 = false := by decide
end Tiny
