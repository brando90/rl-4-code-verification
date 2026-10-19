import Mathlib

namespace Tiny

def solution (x y : Int) : Int := (x + y) * (x - y)

theorem spec_difference_squares (x y : Int) : solution x y = x ^ 2 - y ^ 2 := by
  simp [solution]
  ring

theorem test_positive : solution 5 2 = 21 := by decide
theorem test_negative : solution (-3) 4 = -7 := by decide

end Tiny
#print axioms Tiny.spec_difference_squares
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative
