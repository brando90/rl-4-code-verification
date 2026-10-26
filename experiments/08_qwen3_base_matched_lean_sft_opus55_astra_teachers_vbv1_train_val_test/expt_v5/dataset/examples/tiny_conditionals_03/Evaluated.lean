import Mathlib
namespace Tiny
def solution (x y : Int) : Int := if x <= y then x else y
theorem spec_le_left (x y : Int) : solution x y <= x := by
  by_cases h : x <= y <;> simp [solution, h] <;> omega
theorem test_first : solution 2 5 = 2 := by decide
theorem test_second : solution 5 2 = 2 := by decide
end Tiny
#print axioms Tiny.spec_le_left
#print axioms Tiny.test_first
#print axioms Tiny.test_second
