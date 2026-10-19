import Mathlib
namespace Tiny
def solution (x : Int) : Int := if x >= 0 then x else -x
theorem spec_nonnegative (x : Int) : 0 <= solution x := by
  by_cases h : x >= 0 <;> simp [solution, h] <;> omega
theorem test_positive : solution 4 = 4 := by decide
theorem test_negative : solution (-4) = 4 := by decide
end Tiny
#print axioms Tiny.spec_nonnegative
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative
