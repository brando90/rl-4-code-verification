import Mathlib

namespace Tiny

def solution (x : Int) : Int := x * (x - 1) * (x + 1)

theorem spec_expand (x : Int) : solution x = x ^ 3 - x := by
  simp [solution]
  ring

theorem test_positive : solution 3 = 24 := by decide
theorem test_negative : solution (-2) = -6 := by decide

end Tiny
#print axioms Tiny.spec_expand
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative
