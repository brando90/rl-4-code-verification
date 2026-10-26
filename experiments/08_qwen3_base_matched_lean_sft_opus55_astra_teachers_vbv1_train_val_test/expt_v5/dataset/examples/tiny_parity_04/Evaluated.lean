import Mathlib
namespace Tiny
def solution (x y : Int) : Bool := (x + y) % 2 != 0
theorem spec_commutative (x y : Int) : solution x y = solution y x := by simp [solution, add_comm]
theorem test_odd_sum : solution 2 3 = true := by decide
theorem test_even_sum : solution (-3) 1 = false := by decide
end Tiny
#print axioms Tiny.spec_commutative
#print axioms Tiny.test_odd_sum
#print axioms Tiny.test_even_sum
