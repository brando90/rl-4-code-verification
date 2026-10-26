import Mathlib

namespace Tiny

def solution (x y : Int) : Int := (x + y) ^ 2

theorem spec_binomial (x y : Int) : solution x y = x ^ 2 + 2 * x * y + y ^ 2 := by
  simp [solution]
  ring

theorem test_positive : solution 2 3 = 25 := by decide
theorem test_negative : solution (-4) 1 = 9 := by decide

end Tiny
#print axioms Tiny.spec_binomial
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative
