import Mathlib
namespace Tiny
def solution (x : Int) : Int := if x % 2 == 0 then x + 1 else x
theorem spec_even (x : Int) (h : x % 2 = 0) : solution x = x + 1 := by
  simp [solution, h]
theorem test_even : solution (-4) = -3 := by decide
theorem test_odd : solution (-3) = -3 := by decide
end Tiny
#print axioms Tiny.spec_even
#print axioms Tiny.test_even
#print axioms Tiny.test_odd
