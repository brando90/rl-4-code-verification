import Mathlib

namespace Tiny

def solution (x y : Int) : Int := x ^ 2 - 2 * x * y + y ^ 2

theorem spec_binomial (x y : Int) : solution x y = (x - y) ^ 2 := by
  simp [solution]
  ring

theorem test_positive : solution 5 2 = 9 := by decide
theorem test_negative : solution (-4) 1 = 25 := by decide

end Tiny
#print axioms Tiny.spec_binomial
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative
