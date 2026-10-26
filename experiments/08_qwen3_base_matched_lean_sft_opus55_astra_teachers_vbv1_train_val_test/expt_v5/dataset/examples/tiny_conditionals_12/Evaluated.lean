import Mathlib
namespace Tiny
def solution (x y : Int) : Int := if x == 0 then y else x
theorem spec_zero (y : Int) : solution 0 y = y := by rfl
theorem test_zero : solution 0 9 = 9 := by decide
theorem test_nonzero : solution 3 9 = 3 := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_zero
#print axioms Tiny.test_nonzero
