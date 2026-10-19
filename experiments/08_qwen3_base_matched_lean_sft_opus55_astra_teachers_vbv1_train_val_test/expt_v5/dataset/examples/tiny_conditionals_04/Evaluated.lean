import Mathlib
namespace Tiny
def solution (x y : Int) : Int := if x >= y then x else y
theorem spec_left_le (x y : Int) : x <= solution x y := by
  by_cases h : x >= y <;> simp [solution, h] <;> omega
theorem test_first : solution 5 2 = 5 := by decide
theorem test_second : solution 2 5 = 5 := by decide
end Tiny
#print axioms Tiny.spec_left_le
#print axioms Tiny.test_first
#print axioms Tiny.test_second
