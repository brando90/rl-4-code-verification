import Mathlib
namespace Tiny
def solution (x : Int) : Bool := x % 2 == 0
theorem spec_add_zero (x : Int) : solution (x + 0) = solution x := by simp [solution]
theorem test_even : solution 4 = true := by decide
theorem test_negative_odd : solution (-3) = false := by decide
end Tiny
#print axioms Tiny.spec_add_zero
#print axioms Tiny.test_even
#print axioms Tiny.test_negative_odd
