import Mathlib
namespace Tiny
def solution (x : Int) : Bool := (x * x) % 2 == 0
theorem spec_zero_product (x : Int) : solution (x * 0) = true := by simp [solution]
theorem test_even_square : solution (-4) = true := by decide
theorem test_odd_square : solution 3 = false := by decide
end Tiny
#print axioms Tiny.spec_zero_product
#print axioms Tiny.test_even_square
#print axioms Tiny.test_odd_square
