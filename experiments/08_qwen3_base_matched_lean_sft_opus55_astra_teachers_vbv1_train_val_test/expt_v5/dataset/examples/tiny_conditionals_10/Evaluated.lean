import Mathlib
namespace Tiny
def solution (x : Int) : Int := if x < 0 then 0 else x
theorem spec_nonnegative (x : Int) : 0 <= solution x := by
  by_cases h : x < 0 <;> simp [solution, h] <;> omega
theorem test_negative : solution (-3) = 0 := by decide
theorem test_nonnegative : solution 3 = 3 := by decide
end Tiny
#print axioms Tiny.spec_nonnegative
#print axioms Tiny.test_negative
#print axioms Tiny.test_nonnegative
