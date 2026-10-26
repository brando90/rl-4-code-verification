import Mathlib
namespace Tiny
def solution (x : Int) : Bool := x % 2 != 0
theorem spec_add_zero (x : Int) : solution (x + 0) = solution x := by simp [solution]
theorem test_odd : solution 5 = true := by decide
theorem test_negative_even : solution (-4) = false := by decide
end Tiny
#print axioms Tiny.spec_add_zero
#print axioms Tiny.test_odd
#print axioms Tiny.test_negative_even
