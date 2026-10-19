import Mathlib
namespace Tiny
def solution (x : Int) : Option Int := if 0 <= x then some x else none
theorem spec_nonnegative (x : Int) (h : 0 <= x) : solution x = some x := by simp [solution, h]
theorem test_zero : solution 0 = some 0 := by decide
theorem test_negative : solution (-2) = none := by decide
end Tiny
#print axioms Tiny.spec_nonnegative
#print axioms Tiny.test_zero
#print axioms Tiny.test_negative
