import Mathlib

namespace Tiny

def solution (x y : Int) : Int := x ^ 3 + 3 * x ^ 2 * y + 3 * x * y ^ 2 + y ^ 3

theorem spec_binomial (x y : Int) : solution x y = (x + y) ^ 3 := by
  simp [solution]
  ring

theorem test_positive : solution 1 2 = 27 := by decide
theorem test_negative : solution (-3) 1 = -8 := by decide

end Tiny
